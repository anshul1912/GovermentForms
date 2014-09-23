# coding: utf-8
import tornado.auth
import tornado.web
import tornado

import psycopg2
import logging
import momoko

from datetime import datetime, timedelta
from hashlib import sha512, sha256, md5
from view.common import *

class Home(BaseHandler):
    def get(self):
        name = self.current_user
        if name.get('name', None):
            self.set_cookie('intro_show', '1')
            if name.get('u_type', None) == 'Company':
                self.redirect('/company')
                return
            if name.get('u_type', None) == 'Agent':
                self.redirect('/agent')
                return
            if name.get('u_type', None) == "Customer":
                self.redirect('/customer')
                return

        self.render2("base.html", **{'name': name})

class CPActivationHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if not self.current_user:
            self.set_status(400)
            self.write('Error/400 - Bad request')
            return

        self.flash('info_An activation link has been sent to your email. Please activate your account as soon as possible.')
        self.redirect('/')
        return

class CPForgotPassword(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.current_user:
            self.redirect('/')
            return

        self.flash('info_A password reset link has been sent to your email. Please open your email and click on the link to reset your password.')
        self.redirect('/')
        return

class CPSignupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.current_user:
            self.redirect('/')
            return

        package = 0
        try:
            package = self.get_argument('package')
        except:
            pass

        self.render2("signup.html", **{'package': package})

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        self.check_xsrf_cookie()

        email = self.get_argument("email").lower()

        password = self.get_argument("password")
        password = "%s%s" % (password, self.settings["password_salt"])
        password = sha256(password).hexdigest()

        c_type = self.get_argument("c_type")

        if c_type not in ["Company"]: # ["Customer", "Company"]: # No longer allowing customer signup
            self.set_status(400)
            self.write('Error/400 - Bad request.')
            self.finish()
            return

        if c_type == 'Company':
            try:
                company_name = self.get_argument('company')
                company_addr = self.get_argument('address')
                company_cont = self.get_argument('phone')
            except:
                company_name = "%s's awesome company" % email
                compnay_addr = '<not set>'
                company_cont = email

        gravatar_url = "https://www.gravatar.com/avatar/%s?d=identicon&s=29" % md5(email.lower()).hexdigest()
        sql = (email, password, c_type, gravatar_url, email)
        user = dict(name=email, password=password, c_type=c_type)
        try:
            cursor = yield momoko.Op(self.db.execute,
                "INSERT INTO auth_user (email, password, u_type, avatar) SELECT %s, %s, %s, %s WHERE NOT EXISTS (SELECT email FROM auth_user WHERE email=%s) RETURNING id, name", sql)
        except (psycopg2.Warning, psycopg2.Error) as error:
            logging.error(str(error))
            self.set_status(500)
        else:
            if cursor.rowcount > 0:
                (user_id, user_name) = cursor.fetchone()
                if user.get('c_type') == 'Company':
                    try:
                        sql = (company_name,
                            'Enter some description here', company_addr, company_cont, user_id, user_id)
                        cursor = yield momoko.Op(self.db.execute, """
                            INSERT INTO company (name, description, address, contact, user_id)
                            SELECT %s, %s, %s, %s, %s WHERE NOT EXISTS
                            (SELECT id FROM company WHERE user_id=%s) RETURNING id
                            """, sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        user_key = sha256("%s/%s/%s" % (
                                user.get('name'),
                                user.get('password'),
                                datetime.now().strftime("%Y-%M-%d %H:%M:%S.%s")
                            )).hexdigest()
                        self.mc.hset(user_key, 'id', user_id)
                        self.mc.hset(user_key, 'key', user_key)
                        self.mc.hset(user_key, 'name', user_name or user.get('name'))
                        self.mc.hset(user_key, 'email', user.get('name'))
                        self.mc.hset(user_key, 'avatar', user.get('avatar'))
                        self.mc.hset(user_key, 'u_type', user.get('c_type'))
                        self.mc.expireat(user_key, datetime.now() + timedelta(seconds=self.settings["session_timeout"]))
                        self.set_secure_cookie("u_key", user_key)
                        self.redirect('/')
                        return

                user_key = sha256("%s/%s/%s" % (
                        user.get('name'),
                        user.get('password'),
                        datetime.now().strftime("%Y-%M-%d %H:%M:%S.%s")
                    )).hexdigest()
                self.mc.hset(user_key, 'id', user_id)
                self.mc.hset(user_key, 'key', user_key)
                self.mc.hset(user_key, 'name', user_name or user.get('name'))
                self.mc.hset(user_key, 'email', user.get('name'))
                self.mc.hset(user_key, 'u_type', user.get('c_type'))
                self.mc.expireat(user_key, datetime.now() + timedelta(seconds=self.settings["session_timeout"]))
                self.set_secure_cookie("u_key", user_key)
                self.redirect('/')
            else:
                self.flash('error_A user with that email alreay exists! Try signing in instead.')
                self.redirect('/')
                return

class CPAuthHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        self.check_xsrf_cookie()

        try:
            email = self.get_argument("email")
            password = self.get_argument("password")
        except:
            self.redirect('/')
            return

        password = "%s%s" % (password, self.settings["password_salt"])
        password = sha256(password).hexdigest()

        sql = (email, password)
        user = dict(name=email, password=password)
        try:
            cursor = yield momoko.Op(self.db.execute,
                "SELECT id, name, u_type, activated FROM auth_user WHERE email=%s AND password=%s LIMIT 1", sql)
        except (psycopg2.Warning, psycopg2.Error) as error:
            logging.error(str(error))
            self.set_status(500)
            return
        else:
            if cursor.rowcount > 0:
                (user_id, user_name, user_type, is_activated) = cursor.fetchone()

                if user_type == 'Agent':
                    try:
                        cursor = yield momoko.Op(self.db.execute, """
                                SELECT agent.company_id, agent.department_id, company.name, department.name FROM agent
                                INNER JOIN company ON agent.company_id=company.id
                                INNER JOIN department ON agent.department_id=department.id
                                WHERE agent.user_id=%s
                            """, (user_id, ))
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        return
                    else:
                        if cursor.rowcount > 0:
                            (company_id, department_id, company_name, department_name) = cursor.fetchone()

                user_key = sha256("%s/%s/%s" % (
                        user.get('name'),
                        user.get('password'),
                        datetime.now().strftime("%Y-%M-%d %H:%M:%S.%s")
                    )).hexdigest()
                self.mc.hset(user_key, 'id', user_id)
                self.mc.hset(user_key, 'key', user_key)
                self.mc.hset(user_key, 'name', user_name or user.get('name'))
                self.mc.hset(user_key, 'email', user.get('name'))

                gravatar_url = "https://www.gravatar.com/avatar/%s?d=identicon&s=29" % md5(user.get('name').lower()).hexdigest()
                self.mc.hset(user_key, 'avatar', gravatar_url)

                self.mc.hset(user_key, 'u_type', user_type)

                if user_type == 'Agent':
                    self.mc.hset(user_key, 'company_id', company_id)
                    self.mc.hset(user_key, 'department_id', department_id)
                    self.mc.hset(user_key, 'company_name', company_name)
                    self.mc.hset(user_key, 'department_name', department_name)

                self.mc.expireat(user_key, datetime.now() + timedelta(seconds=self.settings["session_timeout"]))
                self.set_secure_cookie("u_key", user_key)

                if user_type in ['Company', 'Agent']:
                    try:
                        if user_type == 'Company':
                            cursor = yield momoko.Op(self.db.execute, """
                                SELECT logo FROM company WHERE company.user_id=%s LIMIT 1
                                """, (user_id, ))
                        elif user_type == 'Agent':
                            cursor = yield momoko.Op(self.db.execute, """
                                SELECT logo FROM company
                                INNER JOIN agent ON company.id=agent.company_id
                                WHERE agent.user_id=%s
                                LIMIT 1
                                """, (user_id, ))
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        return
                    else:
                        if cursor.rowcount > 0:
                            logo = cursor.fetchone()[0]
                            self.mc.hset(user_key, 'c_logo', logo)

                if not is_activated and user_type == 'Company':
                    self.flash('warning_You account has not been verified yet, some features may not be avaiable. <a href="/activate">Click here to activate your account</a>.')

                self.redirect('/')
            else:
                self.flash('error_That user does not exist or you supplied the wrong credentials, try signing up instead.')
                self.redirect('/')

    def get(self):
        self.redirect('/')

class GoogleAuthHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.gen.coroutine
    def get(self):
        if self.current_user:
            self.redirect('/')
            return

        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            user['c_type'] = "Customer"

            try:
                name = user.get('name')
                email = user.get('email')
                social_id = user.get('claimed_id')
                c_type = user.get('c_type')
                gravatar_url = "https://www.gravatar.com/avatar/%s?d=identicon&s=29" % md5(user.get('email').lower()).hexdigest()
                sql = (name, email, '!', social_id, c_type, gravatar_url, email)
                cursor = yield momoko.Op(self.db.execute,
                    "INSERT INTO auth_user (name, email, password, social_id, u_type, avatar) SELECT %s, %s, %s, %s, %s, %s WHERE NOT EXISTS (SELECT email FROM auth_user WHERE email=%s) RETURNING id", sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    user_id = cursor.fetchone()[0]
                else:
                    try:
                        sql = (user.get('name'), user.get('email'), user.get('c_type'))
                        cursor = yield momoko.Op(self.db.execute,
                            "SELECT id FROM auth_user WHERE name=%s AND email=%s AND u_type=%s LIMIT 1", sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.finish()
                        return
                    else:
                        if cursor.rowcount > 0:
                            user_id = cursor.fetchone()[0]
                        else:
                            self.flash('error_A user with that email already exists!')
                            self.redirect('/')
                            self.finish()
                            return
                user_key = sha256("%s/%s/%s" % (
                        user.get('name'),
                        user.get('claimed_id'),
                        datetime.now().strftime("%Y-%M-%d %H:%M:%S.%s")
                    )).hexdigest()
                self.mc.hset(user_key, 'id', user_id)
                self.mc.hset(user_key, 'key', user_key)
                self.mc.hset(user_key, 'name', user.get('name'))
                self.mc.hset(user_key, 'email', "Google/%s" % user.get('email'))

                self.mc.hset(user_key, 'avatar', user.get('avatar'))

                self.mc.hset(user_key, 'u_type', user.get('c_type'))
                self.mc.expireat(user_key, datetime.now() + timedelta(seconds=self.settings["session_timeout"]))
                self.set_secure_cookie("u_key", user_key)
                self.redirect("/")
            return

        self.authenticate_redirect()

class FacebookAuthHandler(BaseHandler, tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.current_user:
            self.redirect('/')
            return

        if self.get_argument("code", False):
            user = yield self.get_authenticated_user(
                redirect_uri=self.settings["facebook_redirect_uri"],
                client_id=self.settings["facebook_api_key"],
                client_secret=self.settings["facebook_secret"],
                code=self.get_argument("code"))
            user['c_type'] = "Customer"

            try:
                name = user.get('name')
                social_id = user.get('id')
                c_type = user.get('c_type')

                avatar = user.get('picture')
                if avatar:
                    avatar = avatar.get('data')
                    if avatar:
                        avatar = avatar.get('url')

                sql = (name, '%s@chillpublic' % social_id, '!', social_id, c_type, avatar, social_id)
                cursor = yield momoko.Op(self.db.execute,
                    "INSERT INTO auth_user (name, email, password, social_id, u_type, avatar) SELECT %s, %s, %s, %s, %s, %s WHERE NOT EXISTS (SELECT social_id FROM auth_user WHERE social_id=%s) RETURNING id", sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    user_id = cursor.fetchone()[0]
                else:
                    try:
                        sql = (user.get('name'), user.get('id'), user.get('c_type'))
                        cursor = yield momoko.Op(self.db.execute,
                            "SELECT id FROM auth_user WHERE name=%s AND social_id=%s AND u_type=%s LIMIT 1", sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.finish()
                        return
                    else:
                        if cursor.rowcount > 0:
                            user_id = cursor.fetchone()[0]
                        else:
                            self.write('Error/500')
                            self.set_status(500)
                            self.finish()
                            return
                user_key = sha256("%s/%s/%s" % (
                        user.get('name'),
                        user.get('id'),
                        datetime.now().strftime("%Y-%M-%d %H:%M:%S.%s")
                    )).hexdigest()
                self.mc.hset(user_key, 'id', user_id)
                self.mc.hset(user_key, 'key', user_key)
                self.mc.hset(user_key, 'name', user.get('name'))
                self.mc.hset(user_key, 'email', "Facebook/%s" % user.get('id'))
                self.mc.hset(user_key, 'u_type', user.get('c_type'))
                self.mc.expireat(user_key, datetime.now() + timedelta(seconds=self.settings["session_timeout"]))
                self.set_secure_cookie("u_key", user_key)
                self.redirect("/")
        else:
            yield self.authorize_redirect(
                redirect_uri=self.settings["facebook_redirect_uri"],
                client_id=self.settings["facebook_api_key"],
                extra_params={"scope": "read_stream,offline_access"})

class TwitterAuthHandler(BaseHandler, tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.current_user:
            self.redirect('/')
            return

        if self.get_argument("oauth_token", None):
            user = yield self.get_authenticated_user()
            user['c_type'] = "Customer"

            try:
                name = user.get('name')
                social_id = user.get('id_str')
                c_type = user.get('c_type')
                avatar = user.get('profile_image_url_https')
                sql = (name, '%s@chillpublic' % social_id, '!', social_id, c_type, avatar, social_id)
                cursor = yield momoko.Op(self.db.execute,
                    "INSERT INTO auth_user (name, email, password, social_id, u_type, avatar) SELECT %s, %s, %s, %s, %s, %s WHERE NOT EXISTS (SELECT social_id FROM auth_user WHERE social_id=%s) RETURNING id", sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    user_id = cursor.fetchone()[0]
                else:
                    try:
                        sql = (user.get('name'), user.get('id_str'), user.get('c_type'))
                        cursor = yield momoko.Op(self.db.execute,
                            "SELECT id FROM auth_user WHERE name=%s AND social_id=%s AND u_type=%s LIMIT 1", sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.finish()
                        return
                    else:
                        if cursor.rowcount > 0:
                            user_id = cursor.fetchone()[0]
                        else:
                            self.write('Error/500')
                            self.set_status(500)
                            self.finish()
                            return
                user_key = sha256("%s/%s/%s" % (
                        user.get('name'),
                        user.get('id_str'),
                        datetime.now().strftime("%Y-%M-%d %H:%M:%S.%s")
                    )).hexdigest()
                self.mc.hset(user_key, 'id', user_id)
                self.mc.hset(user_key, 'key', user_key)
                self.mc.hset(user_key, 'name', user.get('name'))
                self.mc.hset(user_key, 'email', "Twitter/%s" % user.get('id_str'))
                self.mc.hset(user_key, 'u_type', user.get('c_type'))
                self.mc.expireat(user_key, datetime.now() + timedelta(seconds=self.settings["session_timeout"]))
                self.set_secure_cookie("u_key", user_key)
                self.redirect("/")
        else:
            yield self.authorize_redirect()

class LogoutHandler(BaseHandler):
    def get(self):
        self.mc.delete(self.get_secure_cookie("u_key"))
        self.clear_cookie("u_key")
        self.redirect("/")

class PricingPage(BaseHandler):
    def get(self):
        self.render2('pricing.html')
        return

class PGTest(BaseHandler):
    def get(self):
        key = self.settings['merchant']["key"]

        self.render2('pgtest.html', **{'key': key})
        return

    def post(self):
        context = {}
        key = self.settings['merchant']["key"]
        salt = self.settings['merchant']["salt"]

        try:
            context['firstname'] = self.get_argument('firstname')
            context['phone'] = self.get_argument('phone')
            context['email'] = self.get_argument('email')
            context['key'] = self.get_argument('key')
            context['txnid'] = self.get_argument('txnid')
            context['productinfo'] = self.get_argument('productinfo')
            context['amount'] = self.get_argument('amount')
        except:
            self.set_status(400)
            self.write('Error/400 - Bad request')
            return

        try:
            fid = self.get_argument('fid')
        except:
            if not self.current_user:
                self.write('The following information was received from the payment gateway:<br><br>')
                self.write(str(self.request.body_arguments))
                return
            else:
                # code to process payment details for the current user (company account)

                pass

        context['salt'] = salt
        context['hash'] = sha512("%(key)s|%(txnid)s|%(amount)s|%(productinfo)s|%(firstname)s|%(email)s|||||||||||%(salt)s" % context).hexdigest()
        context['redir'] = True

        self.render2('pgtest.html', **context)