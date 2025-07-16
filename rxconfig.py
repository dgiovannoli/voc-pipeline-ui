import reflex as rx

config = rx.Config(
    app_name="simple_dashboard",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)