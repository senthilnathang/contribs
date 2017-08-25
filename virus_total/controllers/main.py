import base64

import json
import pytz
from datetime import datetime
from psycopg2 import IntegrityError
from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.addons.base.ir.ir_qweb import nl2br
from openerp.addons.website_form.controllers import main
from openerp.addons.virus_scanner.models import virustotal 
from openerp.http import Controller, route
from openerp.addons.base.ir.ir_attachment import ir_attachment
import os

api_key = "6bfc0701dd2a7cd1bfb4642ce83e252f3505e8a6e321a87c3ff4355f3d0968aa"
v = virustotal.VirusTotal(api_key)


class WebsiteFormInherits(main.WebsiteForm):
    # Check and insert values from the form on the model <model>
    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].search([('model', '=', model_name), ('website_form_access', '=', True)])
        if not model_record:
            return json.dumps(False)
        try:
            data = self.extract_data(model_record, ** kwargs)
           
        # If we encounter an issue while extracting data
        except ValidationError, e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields' : e.args[0]})

        try:
            id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
            if id_record:
                self.insert_attachment(model_record, id_record, data['attachments'])
               
         # Some fields have additionnal SQL constraints that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        if data['attachments']:
            for attachment in data['attachments']:
                #~ report= v.scan(data['attachments'][0])
                #~ report=v.get(data['attachments'][0])
                report= v.scan(attachment)
                report=v.get(attachment)
            if report.done:
                report.join()
                assert report.done == True
                print "- Antivirus's positives:", report.positives
            if report.positives ==0 :
                request.session['form_builder_model'] = model_record.name
                request.session['form_builder_id']    = id_record

        return json.dumps({'id': id_record})

    # Extract all data sent by the form and sort its on several properties
    def extract_data(self, model, **kwargs):

        data = {
            'record': {},        # Values to create record
            'attachments': [],  # Attached files
            'custom': '',        # Custom fields values
        }

        authorized_fields = model.sudo()._get_form_writable_fields()
        error_fields = []

        for field_name, field_value in kwargs.items():
            # If the value of the field if a file
            if hasattr(field_value, 'filename'):
                # Undo file upload field name indexing
                field_name = field_name.rsplit('[', 1)[0]

                # If it's an actual binary field, convert the input file
                # If it's not, we'll use attachments instead
                if field_name in authorized_fields and authorized_fields[field_name]['type'] == 'binary':
                    data['record'][field_name] = base64.b64encode(field_value.read())
                else:
                    field_value.field_name = field_name
                    data['attachments'].append(field_value)

            # If it's a known field
            elif field_name in authorized_fields:
                try:
                    input_filter = self._input_filters[authorized_fields[field_name]['type']]
                    data['record'][field_name] = input_filter(self, field_name, field_value)
                except ValueError:
                    error_fields.append(field_name)

            # If it's a custom field
            elif field_name != 'context':
                data['custom'] += "%s : %s\n" % (field_name.decode('utf-8'), field_value)

        # Add metadata if enabled
        environ = request.httprequest.headers.environ
        if(request.website.website_form_enable_metadata):
            data['meta'] += "%s : %s\n%s : %s\n%s : %s\n%s : %s\n" % (
                "IP"                , environ.get("REMOTE_ADDR"),
                "USER_AGENT"        , environ.get("HTTP_USER_AGENT"),
                "ACCEPT_LANGUAGE"   , environ.get("HTTP_ACCEPT_LANGUAGE"),
                "REFERER"           , environ.get("HTTP_REFERER")
            )

        # This function can be defined on any model to provide
        # a model-specific filtering of the record values
        # Example:
        # def website_form_input_filter(self, values):
        #     values['name'] = '%s\'s Application' % values['partner_name']
        #     return values
        dest_model = request.env[model.model]
        if hasattr(dest_model, "website_form_input_filter"):
            data['record'] = dest_model.website_form_input_filter(request, data['record'])

        missing_required_fields = [label for label, field in authorized_fields.iteritems() if field['required'] and not label in data['record']]
        if any(error_fields):
            raise ValidationError(error_fields + missing_required_fields)

        return data
        
        
