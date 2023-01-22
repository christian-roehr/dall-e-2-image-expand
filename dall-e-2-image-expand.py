import os
import argparse

from PIL import Image
from io import BytesIO
import openai

def expand(image, prompt, factor, halign, valign, target_size=1024):

    # Let's require at least 20% expansion in each dimension
    factor = max(1.2, factor)

    # Resize the original image such that it fits into the center of the 1024x1024 output
    (left, upper, right, lower) = image.getbbox()
    width = right - left
    height = lower - upper
    new_height = int(target_size / float(factor) * min(float(height)/width, 1))
    new_width = int(target_size / float(factor) * min(float(width)/height, 1))
    image = image.resize((new_width, new_height))

    # Create a new target sized transparent image and paste the original into it
    buf = Image.new("RGBA", (target_size, target_size), color='#00000000')
    buf.paste(image, box=(int(halign*(target_size - new_width)),
                          int(valign*(target_size - new_height))))
    byte_stream = BytesIO()
    buf.save(byte_stream, format='PNG')
    byte_array = byte_stream.getvalue()

    # Let OpenAI DALL-E 2 fill the masked area with content described by the prompt
    # TODO Request output files as base64 and save the files directly
    try:
        response = openai.Image.create_edit(image=byte_array, prompt=prompt, n=5)
        print(response)
    except openai.error.OpenAIError as e:
        print(e.http_status)
        print(e.error)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Expand an image's surrounding with DALLE-E 2")
    parser.add_argument('-p', dest='prompt', required=True)
    parser.add_argument('-i', dest='image', required=True)
    parser.add_argument('-f', dest='factor', type=float, default=2.0)
    parser.add_argument('-H', dest='halign', type=float, default=0.5,
                        help="Relative horizontal alignment of the original image inside the output image")
    parser.add_argument('-V', dest='valign', type=float, default=0.5,
                        help="Relative vertical alignment of the original image inside the output image")
    args = parser.parse_args()

    openai.api_key = os.getenv("OPENAI_API_KEY")

    with Image.open(args.image) as image:
        expanded_image = expand(image, args.prompt, factor=args.factor,
                                halign=args.halign, valign=args.valign)

