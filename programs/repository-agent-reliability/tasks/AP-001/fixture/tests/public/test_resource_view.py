import unittest

from app.resource_view import ResourceView


class DeferredFetcher:
    def __init__(self):
        self.callbacks = {}

    def __call__(self, resource, callback):
        self.callbacks[resource] = callback

    def resolve(self, resource, value):
        self.callbacks.pop(resource)(value)


class PublicBehaviorTests(unittest.TestCase):
    def test_single_resource_loads(self):
        fetcher = DeferredFetcher()
        view = ResourceView()

        view.select_resource("alpha", fetcher)
        fetcher.resolve("alpha", "ALPHA")

        self.assertEqual(view.current_resource, "alpha")
        self.assertEqual(view.value, "ALPHA")

    def test_completed_request_then_resource_switch(self):
        fetcher = DeferredFetcher()
        view = ResourceView()

        view.select_resource("alpha", fetcher)
        fetcher.resolve("alpha", "ALPHA")
        view.select_resource("beta", fetcher)
        fetcher.resolve("beta", "BETA")

        self.assertEqual(view.current_resource, "beta")
        self.assertEqual(view.value, "BETA")


if __name__ == "__main__":
    unittest.main()
