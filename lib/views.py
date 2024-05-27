from aiohttp.web import Response
from aiohttp.web import View

from aiohttp_jinja2 import render_template

from lib.image import image_to_img_src
from lib.image import PolygonDrawer
from lib.image import open_image


class IndexView(View):
    template = "index.html"

    async def get(self) -> Response:
        return render_template(self.template, self.request, {})

    async def post(self) -> Response:
        try:
            form = await self.request.post()
            image = open_image(form["image"].file)
            draw = PolygonDrawer(image)
            model = self.request.app["model"]
            words = []
            for coords, word, accuracy in model.readtext(image):
                if accuracy >= float(form["accuracy"]):
                    draw.highlight_word(coords, word)
                    cropped_img = draw.crop(coords)
                    cropped_img_b64 = image_to_img_src(cropped_img)
                    words.append(
                        {
                            "image": cropped_img_b64,
                            "word": word,
                            "accuracy": accuracy,
                        }
                    )
            if "is_sorted" in form:
                words.sort(key=lambda x: -x["accuracy"])
            image_b64 = image_to_img_src(draw.get_highlighted_image())
            ctx = {"image": image_b64, "words": words}
        except Exception as err:
            ctx = {"error": str(err), "error_type": type(err).__name__}
        return render_template(self.template, self.request, ctx)
