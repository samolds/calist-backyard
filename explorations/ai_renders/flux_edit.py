"""Edit a photo in-process with FLUX.2 [klein] 4B through mflux (Apple silicon).

The model comes from the shared Hugging Face cache (~/.cache/huggingface/hub, or $HF_HUB_CACHE), the
same pinned download the rora project uses, so it's only on disk once. Memory measures (from rora):
- MLX's pool of freed buffers is capped at 1 GB (by default it keeps everything it ever freed);
- the text encoder is only in memory while it encodes the prompt;
- optionally, the VAE encodes/decodes in tiles (only needed for big images; can leave faint seams).

    ./setup.sh   # one time: env/ and this model (or: env/bin/python explorations/ai_renders/flux_edit.py --download)
"""
import gc
import os
import sys
import tempfile
import time
from pathlib import Path

import truststore

truststore.inject_into_ssl()  # downloads also work on networks that inspect HTTPS

NAME = "FLUX.2 [klein] 4B"
REPO = "black-forest-labs/FLUX.2-klein-4B"
REVISION = "e7b7dc27f91deacad38e78976d1f2b499d76a294"  # the commit mflux 0.23 pins (same as rora)
HUB = Path(os.environ.get("HF_HUB_CACHE")
           or Path(os.environ.get("HF_HOME", "~/.cache/huggingface")) / "hub").expanduser()
PATTERNS = ["model_index.json", "scheduler/*", "text_encoder/*", "tokenizer/*", "transformer/*",
            "vae/*"]
REQUIRED = ["model_index.json", "transformer/diffusion_pytorch_model.safetensors",
            "text_encoder/model.safetensors.index.json", "tokenizer/tokenizer.json",
            "vae/diffusion_pytorch_model.safetensors"]
STEPS = 4  # klein is step-distilled
GUIDANCE = 1.0
MLX_CACHE_BYTES = 1 << 30
OS_RESERVE_GB = 3.0  # what macOS and the window server need to stay responsive


def model_dir() -> Path:
    return HUB / ("models--" + REPO.replace("/", "--")) / "snapshots" / REVISION


def download():
    from huggingface_hub import snapshot_download

    snapshot_download(REPO, revision=REVISION, allow_patterns=PATTERNS, cache_dir=HUB)


def check_ready():
    import platform

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        sys.exit("flux_edit needs a Mac with Apple silicon (mflux).")
    missing = [f for f in REQUIRED if not (model_dir() / f).exists()]
    if missing:
        sys.exit(f"{NAME} isn't downloaded (missing {missing[0]} in {model_dir()}).\n"
                 "Run ./setup.sh (downloads it, ~16 GB).")


def estimate_memory_gb(width: int, height: int, quantize: int, tile: bool) -> float:
    """Peak memory of one edit (whole process), fitted to measurements on this M2 Pro at 4-bit:
    768x576 5.8 GB, 1024x768 7.6 GB, 1024x768 tiled 6.6 GB."""
    f = quantize / 16 + 0.03 if quantize else 1.0
    weights = 7.8 * f + 0.2  # transformer + VAE; the text encoder isn't held during the image work
    vae = 4.6 * width * height / 1e6  # whole-image VAE working memory grows with the area
    return 1.5 + weights + (min(vae, 2.7) if tile else vae)


def check_memory(width: int, height: int, quantize: int, tile: bool, force: bool = False):
    """Stop before loading if the edit can't fit in RAM (heavy swapping can freeze the Mac)."""
    import psutil

    need = estimate_memory_gb(width, height, quantize, tile)
    vm = psutil.virtual_memory()
    total, free = vm.total / 1e9, vm.available / 1e9
    what = f"{NAME} ({quantize or 16}-bit) at {width}x{height} needs about {need:.0f} GB"
    if need > total - OS_RESERVE_GB and not force:
        sys.exit(f"{what}, more than this {vm.total / 2**30:.0f} GB Mac can spare: it would swap "
                 "heavily and could freeze. Use a smaller --max, --tile or --quantize 4, "
                 "or --force to run anyway.")
    if need > free:
        print(f"note: {what}; {free:.0f} GB is free now, so macOS will compress or swap memory "
              "(slower). Closing other apps helps.")


def _free_text_encoder_after_use(model, quantize):
    """Hold the text encoder (~2 GB at 4-bit) only while it encodes the prompt; reload it from
    disk (a few seconds) for the next edit. Uses mflux 0.23 internals."""
    import mlx.core as mx
    from mflux.models.common.weights.loading.weight_applier import WeightApplier
    from mflux.models.common.weights.loading.weight_loader import WeightLoader
    from mflux.models.flux2.model.flux2_text_encoder.qwen3_text_encoder import Qwen3TextEncoder
    from mflux.models.flux2.weights.flux2_weight_definition import Flux2KleinWeightDefinition

    encode = model._encode_prompt_pair

    def load():
        component = next(c for c in Flux2KleinWeightDefinition.get_components()
                         if c.name == "text_encoder")
        weights = WeightLoader.load_single_local(component, model_dir())
        model.text_encoder = Qwen3TextEncoder(**model.model_config.text_encoder_overrides)
        WeightApplier.apply_and_quantize(weights, {"text_encoder": model.text_encoder}, quantize,
                                         Flux2KleinWeightDefinition)

    def encode_then_free(**kwargs):
        if model.text_encoder is None:
            load()
        out = encode(**kwargs)
        mx.eval([x for x in out if isinstance(x, mx.array)])
        model.text_encoder = None
        gc.collect()
        mx.clear_cache()
        return out

    model._encode_prompt_pair = encode_then_free


class Editor:
    """Loads the model once; edit() takes and returns a PIL image."""

    def __init__(self, quantize: int = 4, tile: bool = False):
        import mlx.core as mx
        from mflux.models.common.config.model_config import ModelConfig
        from mflux.models.common.vae.tiling_config import TilingConfig
        from mflux.models.flux2.variants import Flux2KleinEdit

        check_ready()
        mx.set_cache_limit(MLX_CACHE_BYTES)
        self.model = Flux2KleinEdit(quantize=quantize or None, model_path=str(model_dir()),
                                    model_config=ModelConfig.flux2_klein_4b())
        _free_text_encoder_after_use(self.model, quantize or None)
        if tile:
            self.model.tiling_config = TilingConfig()

    def edit(self, image, prompt: str, seed: int, steps: int = STEPS,
             guidance: float = GUIDANCE):
        """`image` is a PIL RGB image whose sides are multiples of 64."""
        with tempfile.TemporaryDirectory(prefix="backyard_edit_") as d:
            path = Path(d) / "in.png"  # mflux reads reference images from files
            image.save(path)
            out = self.model.generate_image(seed=seed, prompt=prompt, num_inference_steps=steps,
                                            height=image.height, width=image.width,
                                            guidance=guidance, image_paths=[path])
        return out.image.convert("RGB")


if __name__ == "__main__":
    if sys.argv[1:] == ["--download"]:
        t = time.time()
        download()
        print(f"{NAME} is in {model_dir()} ({time.time() - t:.0f}s)")
    else:
        sys.exit(__doc__)
