from dotenv import load_dotenv
import numpy as np
import requests
import os
from io import BytesIO
import torch
from diffusers import AutoPipelineForInpainting, DPMSolverMultistepScheduler
from diffusers.utils import load_image
from openai import OpenAI
from PIL import Image # PIL 패키지에서 Image 클래스 불러오기
import cv2
import matplotlib.pyplot as plt
from rembg import remove # rembg 패키지에서 remove 클래스 불러오기


load_dotenv(verbose=True)
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
HF_TOKEN=os.getenv("HF_TOKEN")
def draw_image_by_DALLE(prompt):
    client=OpenAI(api_key=OPENAI_API_KEY)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="hd",
        n=1,
    )
    image_url=response.data[0].url
    return BytesIO(requests.get(image_url).content)

def draw_image_by_SD(prompt):
    # 이미지 경로
    img_path = "sample.jpg"
    # 이미지 파일 불러오기
    img_input = Image.open(img_path)

    # PIL Image를 NumPy 배열로 변환
    out = np.array(remove(img_input))
    mask = (out[:, :, 3] == 0).astype(np.uint8)
    mask_img = Image.fromarray(mask * 255, mode='L')
    pipe = AutoPipelineForInpainting.from_pretrained("diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
                                                    torch_dtype=torch.float16,
                                                    variant="fp16",
                                                    token=HF_TOKEN).to("cuda")
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to("cuda")
    pos = "masterpiece, best quality"
    neg = "worst, bad, (distorted:1.3), (deformed:1.3), (blurry:1.3), out of frame, duplicate"
    img_output = pipe(
        prompt=prompt+','+pos,
        negative_prompt=neg,
        image=img_input,
        mask_image=mask_img,
        num_inference_steps=35,
        strength=0.99,  # make sure to use `strength` below 1.0
        num_images_per_prompt=1
    ).images
    return img_output[0]