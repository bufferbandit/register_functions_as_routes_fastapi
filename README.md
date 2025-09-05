# register_functions_as_routes_fastapi
I really like #Fluidkit kit and the seamless "rpc" architecture, but it required adding route decorators to the functions which kinda took away from the experience so I created this quick utility. Just run register_functions_as_routes(sys.modules[__name__]) and all the routes will be registered
