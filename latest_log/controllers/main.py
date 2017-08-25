

from openerp import http
from openerp.http import request
from openerp.addons import web

class latest_log(web.controllers.main.Binary):

    @http.route('/web/latest_log', type='http', auth="user", csrf=False)    
    def latest_log(self, short_name, name, action, last_log, id, flag):
        latest_log_id = False
        if name:
            Model = request.session.model('latest.log')
            if flag == 'true':                
                latest_log_id = Model.search([('id', '=', id)])
                latest_log_obj = Model.browse(latest_log_id)                
                latest_log_obj.write({
                    'last_log': last_log
                })
            else:                
                latest_log_id = Model.create({
                    'name': name,
                    'short_name': short_name,
                    'user_id': request.session.uid,                    
                    'action': action,                
                    'last_log': last_log
                }, request.context)
            return str(latest_log_id)
        
