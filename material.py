class Material:
    def __init__ (self, id, title, description, img_link, demo_file_link, full_file_link, price):
        self.id = id
        self.title = title
        if description != '':
            self.description = description
        else:
            self.description = '-'
        self.img_link = img_link
        self.demo_file_link = demo_file_link
        self.full_file_link = full_file_link
        self.price = price