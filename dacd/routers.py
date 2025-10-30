class Database2Router:
    route_app_labels = {'dac',}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'dac'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'dac'
        return None