odoo.define('latest_log.LatestLog', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var Widget = require('web.Widget');
var ViewManager = require('web.ViewManager');
var SystrayMenu = require('web.SystrayMenu');
var Model = require('web.DataModel');
var FormView = require('web.FormView');


var LatestLog = Widget.extend({
    template: 'LatestLog',
    init: function(parent) {
        this._super(parent);
        var self = this;
    },
    start: function(){
        this._super();
        self.$records = null
        self.$latest_ul = this.$el.parent().find('.latest_log_li ul');
        self.$no_link = this.$el.parent().find('.latest_log_li ul .no-link');
        self.res_id = false
        this.do_update();
    },  
    set_latest_link: function(breadcrumbs, action){
        var self = this;
        self.short_name = null
        var is_res_id = false;
        if(breadcrumbs.length >= 30){
            var breadcrumbs = String(breadcrumbs)
            var spilt_text = breadcrumbs.split(' / ');
            var last_index = spilt_text.length - 1;
            self.short_name = spilt_text[0] +' / '+ '...' +' / '+ spilt_text[last_index]
        }else{
            self.short_name = breadcrumbs
        }         
        var action_url = null;
        if(action[0].id){
            is_res_id = true;
            action_url = '/web#id='+action[0].id+'&view_type='+action[0].view_type+'&model='+action[0].model;
        }        
        if(action[0].action){
            action_url = action_url + '&action=' + action[0].action;
        }
        if(action[0].active_id){
            action_url = action_url + '&active_id=' + action[0].active_id;
        }        
        new Model('latest.log')
            .query(['name','action','user_id','short_name'])
            .filter([['action', '=', action_url],['user_id', '=', this.session.uid]])
            .all().then(function(records){
                if(records && records.length != 0){
                    (is_res_id) ? self.store_link(self.short_name, breadcrumbs, action_url, records[0].id, true) : false;
                    return false;
                }
                else{
                    (is_res_id) ? self.store_link(self.short_name, breadcrumbs, action_url) : false;
                }
            })
    },
    do_update: function(){
        new Model('latest.log')
            .query(['name','action','user_id','short_name'])
            .filter([['user_id', '=', this.session.uid]])
            .limit(10)
            .order_by('-last_log')
            .all().then(function(records){
                if(records[0]){                                        
                    self.$latest_ul.html(core.qweb.render("LatestLog.li", {'widget': records}));
                }
                else{
                    self.$latest_ul.html(core.qweb.render("LatestLog.li", {'widget': 0}));
                }
            })
            self.breadcrumbs = null;
    },
    store_link: function(short_name, breadcrumbs, action_url, id, flag){
        var self = this;
        var form_data = new FormData();
        var currentdate = new Date(); 
        var currunt_datetime = currentdate.getFullYear() + "/" + (currentdate.getMonth()+1) + "/"
                    + currentdate.getDate() + " " + currentdate.getHours() + ":"  + currentdate.getMinutes() + ":" 
                    + currentdate.getSeconds();
        form_data.append('name',breadcrumbs || false);
        form_data.append('short_name',short_name || false);
        form_data.append('action',action_url || false);
        form_data.append('last_log',currunt_datetime || false);
        form_data.append('flag',flag || false);
        form_data.append('id',id || false);
        $.ajax({
            url: '/web/latest_log',
            type: 'POST',
            data: form_data,
            cache: false,
            processData: false,  
            contentType: false,
            success: function(id){
                if(id){
                    self.do_update();
                }
            }
        });
    },  
});

FormView.include({
    load_record: function(record) {
        var self = this, set_values = [], action_stack = [];
        self._super(record);
        var latest_log = new LatestLog();
        var action = [];
        if(self.ViewManager.active_view && self.ViewManager.active_view.type == 'form'){
            self.breadcrumbs = _.pluck(self.ViewManager.action_manager.get_breadcrumbs(), 'title').join(' / ');

            if(self.ViewManager.action && self.ViewManager.action.target != 'new'){
                action.push({
                'id': self.dataset.ids[self.dataset.index],
                'view_type': self.ViewManager.active_view.type,
                'model': self.ViewManager.action.res_model,
                'menu_id': self.ViewManager.action.menu_id,
                'action': self.ViewManager.action.id,
                'view_mode': self.ViewManager.action.view_mode,
                'active_id': self.ViewManager.action.context.active_id || false
                });
                
                latest_log.set_latest_link(self.breadcrumbs, action);
                return false;
            }
            
        }
    },
});
SystrayMenu.Items.push(LatestLog);
});
