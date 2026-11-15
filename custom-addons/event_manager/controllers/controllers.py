# from odoo import http


# class EventNanager(http.Controller):
#     @http.route('/event_nanager/event_nanager', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/event_nanager/event_nanager/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('event_nanager.listing', {
#             'root': '/event_nanager/event_nanager',
#             'objects': http.request.env['event_nanager.event_nanager'].search([]),
#         })

#     @http.route('/event_nanager/event_nanager/objects/<model("event_nanager.event_nanager"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('event_nanager.object', {
#             'object': obj
#         })

