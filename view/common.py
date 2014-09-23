# coding: utf-8
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import tornado.web

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from datetime import datetime, timedelta
import json

def to_json(object):
    try:
        return json.dumps(object)
    except:
        return json.dumps(["Cannot make JSON from that object"])

class TemplateRendering:
    """
    A simple class to hold methods for rendering templates.
    """
    def render_template(self, template_name, **kwargs):
        template_dirs = []
        if self.settings.get('template_path', ''):
            template_dirs.append(
                self.settings["template_path"]
            )

        env = Environment(
            loader=FileSystemLoader(template_dirs),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True)
        env.filters.update({
                'to_json': to_json
            })

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        content = template.render(kwargs)
        return content

class BaseHandler(tornado.web.RequestHandler, TemplateRendering):
    @property
    def db(self):
        return self.application.db

    @property
    def mc(self):
        return self.application.mc

    def flash(self, message):
        self.set_cookie('flash', tornado.escape.url_escape(message))

    def get_current_user(self):
        user_key = self.get_secure_cookie("u_key")
        self.mc.expireat(user_key, datetime.now() + timedelta(seconds=self.settings["session_timeout"]))
        user = self.mc.hgetall(user_key)
        return user

    """
    RequestHandler already has a `render()` method. I'm writing another
    method `render2()` and keeping the API almost same.
    """
    def render2(self, template_name, **kwargs):
        """
        This is for making some extra context variables available to
        the template
        """
        kwargs.update({
            'settings': self.settings,
            'STATIC_URL': self.settings.get('static_url_prefix', '/static/'),
            'request': self.request,
            'xsrf_token': self.xsrf_token,
            'xsrf_form_html': self.xsrf_form_html,
        })
        content = self.render_template(template_name, **kwargs)
        self.write(content)
