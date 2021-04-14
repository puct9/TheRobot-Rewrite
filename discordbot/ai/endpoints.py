import json
import io
import os
from typing import Sequence

import discord
import httpx
import torch
from PIL import Image, UnidentifiedImageError
from torchvision import models, transforms

from ..routing import Endpoint

inception_v3 = models.inception_v3(
    pretrained=True, transform_input=True
).eval()
imagenet_mapping = {
    int(ind): name
    for ind, (_, name) in json.load(
        open(
            os.path.join(
                os.path.dirname(__file__), "imagenet_class_index.json"
            )
        )
    ).items()
}


@Endpoint
async def inception_v3_inference(
    client: discord.Client, message: discord.Message, groups: Sequence[str]
) -> None:
    if len(message.attachments) != 1:
        await message.channel.send("No image attached")
        return
    try:
        async with httpx.AsyncClient() as httpclient:
            req = await httpclient.get(message.attachments[0].url)
    except Exception:
        await message.channel.send("Unable to download image")
        return
    try:
        img = Image.open(io.BytesIO(req.content))
    except UnidentifiedImageError:
        await message.channel.send("Unable to open image")
        return
    to_tensor = transforms.Compose(
        [
            transforms.Resize(299),
            transforms.CenterCrop(299),
            transforms.ToTensor(),
        ]
    )
    image_tensor = to_tensor(img).unsqueeze(0)
    output = inception_v3(image_tensor)[0]
    probs = torch.softmax(output, 0)
    argmax = torch.argmax(probs, 0).item()
    name = imagenet_mapping[argmax]
    prob = probs[argmax]
    await message.channel.send(f"{(prob * 100):.1f}% {name}")
