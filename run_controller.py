from os_ken.base import app_manager


def main():
    manager = app_manager.AppManager.get_instance()

    manager.load_apps([
        'controller.qos_controller'
    ])

    manager.instantiate_apps()


if __name__ == '__main__':
    main()
