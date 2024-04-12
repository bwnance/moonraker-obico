import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Pango
from ks_includes.screen_panel import ScreenPanel
import qrcode
from io import BytesIO
import logging
import requests
import gi
from gi.repository import Gtk, GdkPixbuf, Pango

OBICO_LINK_STATUS_MACRO = 'OBICO_LINK_STATUS'

class Panel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)

        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content.add(self.main_container)

        self.top_box_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_container.add(self.top_box_container)

        qr_code_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        qr_code_container.set_margin_top(10)
        qr_code_container.set_margin_bottom(10)
        self.top_box_container.pack_start(qr_code_container, True, False, 0)
        self.qr_code_label = self.create_label()
        qr_code_container.pack_start(self.qr_code_label, False, True, 0)
        self.qr_image = Gtk.Image()
        aspect_frame = Gtk.AspectFrame.new(None, 0.5, 0.5, 1.0, False)
        aspect_frame.add(self.qr_image)
        self.qr_image.set_hexpand(True)
        self.qr_image.set_vexpand(True)
        qr_code_container.pack_start(aspect_frame, True, True, 0)

        self.content.show_all()

    def activate(self):
        logging.info('activate')

        gcode_macros = self._printer.get_gcode_macros()
        gcode_macros_lower = [macro.lower() for macro in gcode_macros]

        if OBICO_LINK_STATUS_MACRO not in [macro.upper() for macro in gcode_macros]:
            self.display_setup_guide_qr_code()

        else:
            moonraker_config = self.get_connected_moonraker_config(self._screen)
            moonraker_host = moonraker_config.get('moonraker_host', '127.0.0.1')
            moonraker_port = moonraker_config.get('moonraker_port', 7125)

            url = f'http://{moonraker_host}:{moonraker_port}/printer/objects/query?gcode_macro%20{OBICO_LINK_STATUS_MACRO}'

            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            logging.info(data)

            is_linked = data.get('result', {}).get('status', {}).get('gcode_macro OBICO_LINK_STATUS', {}).get('is_linked')
            one_time_passcode = data.get('result', {}).get('status', {}).get('gcode_macro OBICO_LINK_STATUS', {}).get('one_time_passcode')
            one_time_passlink = data.get('result', {}).get('status', {}).get('gcode_macro OBICO_LINK_STATUS', {}).get('one_time_passlink')
            if is_linked is None:
                self.display_setup_guide_qr_code()
            elif is_linked:
                self.display_linked_status()
            elif one_time_passcode and one_time_passlink: # these 2 fields should be available together. But just in case
                self.display_link_qr_code(one_time_passcode, one_time_passlink)
            else:
                self.display_setup_guide_qr_code()

    def display_linked_status(self):
        self.qr_code_label.set_markup(f"<big></big>")

        self.reset_action_container()
        setup_label1 = self.create_label()
        setup_label1.set_markup(f"<big>Printer is linked to Obico server.</big>")

        self.update_qr_code('https://obico.io/')

    def display_link_qr_code(self, one_time_passcode, one_time_passlink):
        self.qr_code_label.set_markup(f"<big><b>Scan to Link Obico</b></big>")

        self.reset_action_container()

        self.update_qr_code(one_time_passlink)

    def display_setup_guide_qr_code(self):
        self.qr_code_label.set_markup(f"<big><b>Scan to Set Up Obico</b></big>")
        self.reset_action_container()

        self.update_qr_code('https://obico.io/docs/user-guides/klipper-screen-setup/')

        self.default_bottom_text()

    def update_qr_code(self, link_url):
        # Generate a QR code
        # qr = qrcode.QRCode(
        #     version=1,
        #     error_correction=qrcode.constants.ERROR_CORRECT_L,
        #     box_size=10,
        #     border=4,
        # )
        # qr.add_data(link_url)
        # qr.make(fit=True)

        # img = qr.make_image(fill_color="black", back_color="white")
        # img_byte_arr = BytesIO()
        # img.save(img_byte_arr, format='PNG')
        # img_byte_arr = img_byte_arr.getvalue()

        # # Load the QR code image into a GdkPixbuf
        # loader = GdkPixbuf.PixbufLoader.new_with_type('png')
        # loader.write(img_byte_arr)
        # loader.close()
        # pixbuf = loader.get_pixbuf()

        # # Set the QR code to the image widget
        # self.qr_image.set_from_pixbuf(pixbuf)

        if self._screen.vertical_mode:
            width = self._screen.width * 0.9
            height = self._screen.height / 4
        else:
            width = self._screen.width * .25
            height = self._gtk.content_height * 0.47
        filename = '/home/biqu/KlipperScreen/./docs/img/panels/extrude.png'
        # pixbuf = self.get_file_image('/home/biqu/KlipperScreen/./docs/img/panels/console.png', width, height)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, int(width), int(height))

        self.qr_image.set_from_pixbuf(pixbuf)


    def reset_action_container(self):
        pass

    def create_label(self):
        label = Gtk.Label()
        label.set_line_wrap(True)  # Enable line wrapping
        label.set_line_wrap_mode(Pango.WrapMode.WORD)  # Break lines at word boundaries
        return label

    def default_bottom_text(self):
        pass

    def get_connected_moonraker_config(self, _screen):
        connected_printer_name = _screen.connected_printer
        connected_printer_dict = {}

        for printer in _screen._config.get_printers():
            if connected_printer_name in printer.keys():
                connected_printer_dict = printer[connected_printer_name]
                break
        return connected_printer_dict
