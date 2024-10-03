from ..global_py import Config  # noqa
from odoo import api, fields, models  # noqa


class BaseURLEditor(models.Model):
    _name = 'gts_whatsapp.base_url_editor'

    def get_default(self):
        return Config().get('base_url')

    base_url = fields.Char(string='Base URL', required=True, default=get_default)

    @api.onchange('base_url')
    def onchange_base_url(self):
        if self.base_url:
            if self.base_url.endswith('/'):
                self.base_url.removesuffix('/')

            Config().set('base_url', self.base_url)

    def reset(self):
        Config().set('base_url', 'https://whatapi.geektechsol.com')
        self.base_url = Config().get('base_url')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Whatsapp Base URL Editor',
            'view_mode': 'form',
            'res_model': 'gts_whatsapp.base_url_editor',
            'target': 'new',
            'res_id': self.id
        }