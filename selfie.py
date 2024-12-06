import datetime
import hashlib
import io
import os

import matplotlib
import numpy as np
import pandas as pd
import psycopg2
from PIL import Image
from atproto import Client, client_utils, models
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname="bsky_feeds",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)


def generate_graphic(date_str):
    query = f"SELECT created_at, language FROM posts WHERE created_at::date = '{date_str}';"

    df = pd.read_sql_query(query, conn)
    df = df.sort_values(by='created_at')

    color_map = {
        lang: get_color_for_language(lang) for lang in df['language'].unique()
    }

    grid = [
        color_map[language]
        for language in df['language']
    ]

    n_posts = len(df)
    grid_cols = int(np.ceil(np.sqrt(n_posts)))  # Number of columns
    grid_rows = int(np.ceil(n_posts / grid_cols))  # Number of rows

    grid_to_png(grid, grid_rows, grid_cols, f"images/posts_{date_str}.png")


def get_color_for_language(language_code):
    """
    Assigns an RGB color to a language based on its ISO 639-1 code.

    Args:
      language_code: The ISO 639-1 code of the language.

    Returns:
      A color in RGB tuple format, e.g., (255, 0, 0) for red.
    """

    if not language_code:
        return 128, 128, 128  # gray

    common_language_colors = {
        'en': (0, 80, 255),  # Blue for English
        'es': (255, 0, 0),  # Red for Spanish
        'fr': (75, 0, 130),  # Indigo for French
        'de': (255, 255, 0),  # Yellow for German
        'zh': (255, 165, 0),  # Orange for Chinese
        'ja': (0, 255, 0),  # Green for Japanese
        'ru': (0, 255, 255),  # Cyan for Russian
        'pt': (255, 105, 180),  # Hot pink for Portuguese
        'ar': (255, 215, 0),  # Gold for Arabic
        'hi': (0, 255, 127),  # Spring Green for Hindi
    }
    if language_code in common_language_colors:
        return common_language_colors[language_code]

    # Create a colormap
    cmap = matplotlib.colormaps.get_cmap('hsv')

    # Create a simple hash function to map language codes to numbers
    def hash_language(language_code):
        md5_hash = hashlib.md5(language_code.encode()).hexdigest()
        return (int(md5_hash, 16) + 200) % 256

    # Map the hashed value to a color using the colormap
    color_index = hash_language(language_code) / 256
    color = cmap(color_index)[:3]  # Extract RGB values (values in range [0, 1])

    # Convert the RGB values to integers in the range [0, 255]
    rgb_color = tuple(int(c * 255) for c in color)

    return rgb_color


def grid_to_png(rgb_colors, image_width, image_height, output_filename):
    # Create a new image in RGB mode
    image = Image.new("RGB", (image_width, image_height))

    # Put the data into the image (it's faster and more memory-efficient)
    image.putdata(rgb_colors)

    # Save the image as a PNG file
    image.save(output_filename)


def main():
    yesterday = datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    generate_graphic(yesterday_str)

    client = Client()
    client.login(
        os.environ["BSKY_USER"],
        os.environ["BSKY_PASSWORD"],
    )

    im = Image.open(f"images/posts_{yesterday_str}.png")
    img_byte_arr = io.BytesIO()
    im.save(img_byte_arr, quality=20, optimize=True, format='JPEG')
    img_data = img_byte_arr.getvalue()

    post = client.send_image(
        text=yesterday_str,
        image=img_data,
        image_alt='Selfie of Bluesky. Each dot represents a post, sorted chronologically, top-down, left-right. Color corresponds to the language.',
    )
    post_ref = models.create_strong_ref(post)

    text_builder = client_utils.TextBuilder()
    text_builder.text('Download the full resolution image ')
    text_builder.link(
        'at this link',
        f'https://github.com/ealmuina/bsky-selfies/blob/main/images/posts_{yesterday_str}.png',
    )
    client.send_post(
        text_builder,
        reply_to=models.AppBskyFeedPost.ReplyRef(parent=post_ref, root=post_ref),
    )


if __name__ == "__main__":
    main()
