import asyncio
class MyModel:
    def __init__(self, url2):
        self.url2 = url2
        self.model = None
        self.webcam = None
        self.label_container = None
        self.max_predictions = None

    async def init(self):
        print('got here')
        model_url = f"{self.url2}model.json"
        metadata_url = f"{self.url2}metadata.json"

        # Load the model and metadata
        self.model = await load_model(model_url, metadata_url)
        self.max_predictions = self.model.get_total_classes()

        # Setup a webcam
        flip = True  # whether to flip the webcam
        self.webcam = Webcam(200, 200, flip)  # width, height, flip
        await self.webcam.setup()  # request access to the webcam
        await self.webcam.play()

        # Start the prediction loop
        asyncio.create_task(self.loop())

        # Append elements to the DOM (this part may require a web framework)
        self.label_container = document.getElementById("label-container")
        for i in range(self.max_predictions):
            class_div = document.createElement("div")
            class_div.id = f"class{i}"
            self.label_container.appendChild(class_div)

    async def loop(self):
        while True:
            await self.webcam.update()  # Update the webcam frame
            await self.predict()
            await asyncio.sleep(0)  # Yield control to the event loop

    async def predict(self):
        # Predict can take in an image, video, or canvas HTML element
        prediction = await self.model.predict(self.webcam.canvas)
        for i in range(self.max_predictions):
            class_prediction = f"{prediction[i]['className']}: {prediction[i]['probability']:.2f}"
            self.label_container.childNodes[i].innerHTML = class_prediction

# Usage
s = MyModel('hi')
