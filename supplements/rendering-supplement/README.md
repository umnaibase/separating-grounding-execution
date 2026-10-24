# Document-image rendering reproduction

This supplement provides the supplied renderer and an unchanged copy of the 25 source-document records used in the archived Claude Fable 5.1 image-extraction condition. It accompanies frozen release 1.2.2; the frozen release and its model results are unchanged.

Regeneration reproduced all 25 archived PNGs byte for byte. The decoded pixels, dimensions and image modes also matched for every document. `rendering_verification.json` records the document order, script and input hashes, font hashes, runtime versions and individual image comparisons.

The verification used Python 3.12.14, Pillow 12.3.0, FreeType 2.14.3 and the DejaVu font files at `/usr/share/fonts/truetype/dejavu`. These are the verification environment's versions; they do not independently attest the environment of the earlier model run.

## Reproduce the images

Install Pillow 12.3.0 and Debian's `fonts-dejavu-core` package, then run from this directory:

```bash
python3 -m pip install -r requirements.txt
python3 render_images.py --docs prompts/extraction_docs.jsonl --output images
```

Use the JSONL records in their archived order. The seeded random generator advances across documents, so sorting or otherwise reordering the records changes the images.

The exact font-file SHA-256 values used in the verified run are:

| Font | SHA-256 |
| --- | --- |
| DejaVuSerif.ttf | `8f2c103bfa3fd5de71f1b92b18f21906b5a26871fb7e19a9a4c9af539c3cc7ab` |
| DejaVuSerif-Bold.ttf | `847b33e13925f19ff87e4d934d6b3cf7cac35ce16424f6f670e40c2f377cf2df` |
| DejaVuSansMono.ttf | `c805f9436dbc268644c1d9584f01a601a653e028e08fd74b9b949f6cf8304d88` |

## Scope

This check reproduces rendering only. It adds no model calls or scores, does not test realistic scans and does not verify the earlier model's runtime image delivery. The source JSONL contains archived truth fields and belongs in reproduction material; it must not be supplied as an input to a blinded evaluation.
