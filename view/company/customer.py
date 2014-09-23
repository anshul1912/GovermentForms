# coding: utf-8

from .__init__ import *
from chat import global_agent_buffer

class Customer(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, section=None):
        name = self.current_user

        if name.get('u_type') != 'Customer':
            self.write('403 - Forbidden')
            self.set_status(403)
            self.finish()
            return

        if section == 'profile':
            self.render2('company/customer/profile.html', **{'name': name})
            return

        if section == 'tickets':
            tickets = []
            try:
                sql = (name.get('id'), )
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT ticket.id, ticket.title, ticket.timestamp, ticket.status
                    FROM ticket WHERE ticket.status != 'close' AND ticket.user_id=%s
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    tickets = cursor.fetchall()

                self.render2('company/tickets/tickets-customer.html', **{'name': name, 'tickets': tickets})

            return

        if section == 'solved':
            tickets = []
            try:
                sql = (name.get('id'), )
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT ticket.id, ticket.title, ticket.timestamp, ticket.status
                    FROM ticket WHERE ticket.status = 'close' AND ticket.user_id=%s
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    tickets = cursor.fetchall()

                self.render2('company/customer/resolved.html', **{'name': name, 'tickets': tickets})

            return

        if section == 'tickets/view':
            try:
                ticket_id = self.get_argument('ticket')
            except:
                self.redirect('/customer/tickets')
                return

            try:
                form_id = self.get_argument('form')
            except:
                form_id = None

            if form_id: # form viewer
                sql = (form_id, ticket_id, name.get('id'))
                self.db.execute("""
                    SELECT data, markup, ticket_id FROM form_data
                    INNER JOIN ticket ON form_data.ticket_id=ticket.id
                    INNER JOIN auth_user ON ticket.user_id=auth_user.id
                    WHERE form_data.id=%s AND ticket.id=%s AND auth_user.id=%s
                """, sql, callback=(yield gen.Callback('q1')))

                self.db.execute("""
                    SELECT filename, filepath, content_type FROM attachment WHERE ticket_id=%s
                """, (ticket_id, ), callback=(yield gen.Callback('q2')))

                self.db.execute("""
                    SELECT company.logo FROM company INNER JOIN ticket ON ticket.company_id=company.id where ticket.id=%s
                """, (ticket_id, ), callback=(yield gen.Callback('q3')))

                try:
                    cursor_q1, cursor_q2, cursor_q3 = yield momoko.WaitAllOps(('q1', 'q2', 'q3'))
                except (psycopg2.Warning, psycopg2.Error) as error:
                    logging.error(str(error))
                    self.set_status(500)
                    self.write('Error/500')
                    self.finish()
                    return
                else:
                    if cursor_q1.rowcount > 0:
                        form_data = cursor_q1.fetchone()

                        attachments = []
                        if cursor_q2.rowcount > 0:
                            attachments = cursor_q2.fetchall()

                        c_logo = None
                        if cursor_q3.rowcount > 0:
                            c_logo = cursor_q3.fetchone()[0]

                        self.render2('company/forms/form-viewer-customer.html', **{
                                'name': name,
                                'form_data': form_data,
                                'attachments': attachments,
                                'c_logo': c_logo,
                            })
                        return
                    else:
                        self.set_status(404)
                        self.write('Not found/404')
                        return

            sql = (ticket_id, name.get('id'))
            self.db.execute("""
                    SELECT * FROM ticket WHERE ticket.id=%s AND
                    ticket.user_id=%s LIMIT 1
                """, sql, callback=(yield gen.Callback('q1')))

            self.db.execute("""
                    SELECT ticket_thread.description,
                    auth_user.name, auth_user.email,
                    ticket_thread.timestamp, ticket_thread.id
                    FROM ticket_thread
                    INNER JOIN auth_user ON ticket_thread.user_id=auth_user.id
                    WHERE ticket_thread.ticket_id=%s ORDER BY timestamp
                """, (ticket_id, ), callback=(yield gen.Callback('q2')))

            self.db.execute("""
                    SELECT filename, filepath, thread_id FROM attachment WHERE ticket_id=%s
                """, (ticket_id, ), callback=(yield gen.Callback('q3')))

            self.db.execute("""
                    SELECT id FROM form_data WHERE ticket_id=%s
                """, (ticket_id, ), callback=(yield gen.Callback('q4')))

            try:
                cursor_q1, cursor_q2, cursor_q3, cursor_q4 = yield momoko.WaitAllOps(('q1', 'q2', 'q3', 'q4'))
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor_q1.rowcount > 0:
                    ticket = cursor_q1.fetchone()
                    ticket_thread = []
                    if cursor_q2.rowcount > 0:
                        ticket_thread = cursor_q2.fetchall()
                    attachment = None
                    if cursor_q3.rowcount > 0:
                        attachment = cursor_q3.fetchall()
                    form_data = None
                    if cursor_q4.rowcount > 0:
                        form_data = cursor_q4.fetchone()[0]
                    if ticket[7] == 'live':
                        global_agent_buffer.broadcast({
                            'ticket': {
                                'id': ticket[0],
                                'title': ticket[1],
                                'timestamp': ticket[6].strftime("%Y-%m-%d %H:%M:%S")
                            },
                            'company_id': ticket[3],
                            'department_id': ticket[4],
                            'status': 'live',
                        })
                    self.render2('company/tickets/ticket-view-customer.html', **{
                            'name': name,
                            'ticket': ticket,
                            'thread': ticket_thread,
                            'attachment': attachment,
                            'form_data': form_data,
                        })
                    return
                else:
                    self.redirect('/customer/tickets')
                    return

        if section == 'forms':
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    d_query = self.get_argument('json')
                    company_id = self.get_argument('company')
                    department_id = self.get_argument('department')
                except:
                    self.set_status(403)
                    self.write('403/Forbidden')
                    return

                try:
                    sql = (company_id, department_id)
                    cursor = yield momoko.Op(self.db.execute, """
                            SELECT form.id, form.title FROM form WHERE
                            form.company_id=%s AND form.department_id=%s
                        """, sql)
                except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                else:
                    if cursor.rowcount > 0:
                        data = cursor.fetchall()
                        self.write(json.dumps(data))
                        return

            self.render2('company/customer/forms.html', **{'name': name})
            return

        if section == 'forms/view':
            try:
                company_id = self.get_argument('company')
                department_id = self.get_argument('department')
                form_id = self.get_argument('form')
            except:
                self.redirect('/customer/forms')
                return

            try:
                sql = (company_id, department_id, form_id)
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT form.id, form.title, form.content, form.department_id, form.company_id, company.logo
                    FROM form INNER JOIN company ON form.company_id=company.id
                    WHERE form.company_id=%s AND form.department_id=%s AND form.id=%s LIMIT 1
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    form = cursor.fetchone()
                    self.render2('company/forms/form-view-customer.html', **{
                            'name': name,
                            'form': form
                        })
                    return
                else:
                    self.redirect('/customer/forms')
                    return

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                d_query = self.get_argument('json')
            except:
                self.set_status(403)
                self.write('403/Forbidden')
                return

            try:
                if d_query == 'companies':
                    cursor = yield momoko.Op(self.db.execute, """
                        SELECT company.id, company.name FROM company
                        """)
                elif d_query == 'departments':
                    try:
                        company_id = self.get_argument('id')
                    except:
                        self.set_status(400)
                        return
                    cursor = yield momoko.Op(self.db.execute, """
                        SELECT department.id, department.name FROM department
                        WHERE department.company_id=%s
                        """, (company_id, ))
                else:
                    self.set_status(400)
                    return

            except (psycopg2.Warning, psycopg2.Error) as error:
                    logging.error(str(error))
                    self.set_status(500)
                    self.write('Error/500')
                    self.finish()
                    return
            else:
                if cursor.rowcount > 0:
                    data = cursor.fetchall()
                    self.write(json.dumps(data))
                    return

        self.render2('company/customer/dashboard.html', **{'name': name})

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self, section=None):
        self.check_xsrf_cookie()

        name = self.current_user

        if name.get('u_type') != 'Customer':
            self.write('403 - Forbidden')
            self.set_status(403)
            self.finish()
            return

        if section == 'profile':
            try:
                customer = self.get_argument('customer')
                password = self.get_argument('password')
            except:
                self.redirect('/customer/profile')
                return

            if len(password) > 0:
                password = "%s%s" % (password, self.settings["password_salt"])
                password = sha256(password).hexdigest()

            try:
                if len(password) > 0:
                    sql = (customer, password, name.get('id'))
                    cursor = yield momoko.Op(self.db.execute, """
                        UPDATE auth_user SET name=%s, password=%s WHERE id=%s RETURNING name
                        """, sql)
                else:
                    sql = (customer, name.get('id'))
                    cursor = yield momoko.Op(self.db.execute, """
                        UPDATE auth_user SET name=%s WHERE id=%s RETURNING name
                        """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    user_name = cursor.fetchone()[0]
                    self.mc.hset(name.get('key'), 'name', user_name)
                    self.redirect('/customer/profile')
                    return
                else:
                    self.write('Unspecified error')
                    self.set_status(500)
                    self.finish()
                    return

        if section == 'tickets/view':
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    ticket_id = self.get_argument('ticket')
                    ticket_state = self.get_argument('state')
                except:
                    self.set_status(400)
                    return

                if ticket_state == 'open':
                    try:
                        sql = ('open', ticket_id, name.get('id'))
                        cursor = yield momoko.Op(self.db.execute, """
                            UPDATE ticket SET status=%s WHERE id=%s AND user_id=%s RETURNING id, company_id, department_id
                            """, sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        self.set_status(200)
                        (tid, cid, did) = cursor.fetchone()
                        global_agent_buffer.broadcast({
                            'ticket': {
                                'id': tid,
                            },
                            'company_id': cid,
                            'department_id': did,
                            'status': 'open',
                        })
                        self.finish()
                        return

            message = None
            try: # trapping going public here
                message = self.get_argument('p_message')
                ticket_id = self.get_argument('tid')
            except:
                pass

            if message:
                sql = (message, ticket_id, name.get('id'), ticket_id)
                try:
                    cursor = yield momoko.Op(self.db.execute, """
                            INSERT INTO forum (message, ticket_id, user_id)
                            SELECT %s, %s, %s WHERE NOT EXISTS
                            (SELECT ticket_id FROM forum WHERE ticket_id=%s) RETURNING id
                        """, sql)
                except (psycopg2.Warning, psycopg2.Error) as error:
                    logging.error(str(error))
                    self.set_status(500)
                    self.write('Error/500')
                    self.finish()
                    return
                else:
                    if cursor.rowcount > 0:
                        forum_id = cursor.fetchone()
                        self.redirect('/public/%s' % ticket_id)
                        return
                    else:
                        self.flash('error_A forum topic already exists for this ticket.')
                        self.redirect('/customer/tickets/view?ticket=%s' % ticket_id)

            try:
                comment = self.get_argument('comment')
                ticket_id = self.get_argument('tid')

                upload = None
                if len(self.request.files.keys()):
                    upload = self.request.files.get('upload')
                    if upload is not None:
                        upload_name = upload[0]['filename']
                        upload_mime = upload[0]['content_type']
                        upload_data = upload[0]['body']
            except:
                self.flash('error_Wrong input supplied.')
                self.redirect('/customer/tickets')
                return

            if not len(comment) > 0:
                self.flash('warning_Please enter some comment.')
                self.redirect('/customer/tickets/view?ticket=%s' % ticket_id)
                return

            try:
                sql = (comment, ticket_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                        INSERT INTO ticket_thread (ticket_id, description, user_id)
                        SELECT ticket.id, %s, ticket.user_id FROM ticket
                        WHERE ticket.id=%s AND ticket.user_id=%s LIMIT 1 RETURNING id, timestamp
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    (thread_id, t_stamp) = cursor.fetchone()
                    if upload is not None:
                        try:
                            file_ext = upload_name.split('.')
                            if len(file_ext) == 1:
                                file_ext = 'bin'
                            else:
                                file_ext = file_ext[-1][:4]

                            upload_path = "%s.%s" % (sha256("%s/%s" % (upload_name, datetime.now())).hexdigest(), file_ext)
                            sql = (upload_name, upload_path, upload_mime, ticket_id, thread_id)
                            cursor = yield momoko.Op(self.db.execute, """
                                    INSERT INTO attachment (filename, filepath, content_type, ticket_id, thread_id)
                                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                                """, sql)
                        except (psycopg2.Warning, psycopg2.Error) as error:
                            logging.error(str(error))
                            self.set_status(500)
                            self.write('Error/500')
                            self.finish()
                            return
                        else:
                            if cursor.rowcount > 0:
                                filepath = os.path.join(self.settings["upload_path"], upload_path)
                                with open(filepath, 'wb') as f:
                                    f.write(upload_data)

                    if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        self.write(t_stamp.strftime("%H:%M:%S"))
                        return

                    self.redirect('/customer/tickets/view?ticket=%s' % ticket_id)
                    return
                else:
                    self.set_status(500)
                    self.write('Error/500')
                    return

        if section == 'solved':
            try:
                action = self.get_argument('action')
                ticket_id = self.get_argument('tid')
            except:
                self.flash('error_Wrong input supplied')
                self.set_status(400)
                return

            if action not in ['praise', 're-open']:
                self.set_status(400)
                self.write('400/Bad request')
                return

            if action == 're-open':
                try:
                    sql = (action, ticket_id, name.get('id'))
                    cursor = yield momoko.Op(self.db.execute, """
                        UPDATE ticket SET status=%s WHERE id=%s and user_id=%s RETURNING id
                    """, sql)
                except (psycopg2.Warning, psycopg2.Error) as error:
                    logging.error(str(error))
                    self.set_status(500)
                    self.write('Error/500')
                    self.finish()
                    return
                else:
                    if cursor.rowcount > 0:
                        ticket_id = cursor.fetchone()[0]
                        self.redirect('/customer/tickets/view?ticket=%s' % ticket_id)
                        return
                    else:
                        self.set_status(500)
                        self.write('Error/500')
                        return

            elif action == 'praise':
                self.flash('info_Thank you for your feedback.')
                self.set_status(200)
                return

            return

        if section == 'forms/view':
            try:
                form_id = self.get_argument('fid')
                company_id = self.get_argument('cid')
                department_id = self.get_argument('did')
                input_dict = self.request.arguments
            except:
                self.set_status(400)
                self.write('Error/400')
                return

            _xsrf = input_dict.pop('_xsrf', None)[0]
            input_dict.pop('form', None)
            input_dict.pop('fid', None)
            input_dict.pop('cid', None)
            input_dict.pop('did', None)
            input_dict.pop('company', None)
            input_dict.pop('department', None)
            form_markup = input_dict.pop(_xsrf, [None])[0]

            try:
                form_markup = unquote(form_markup)
            except:
                form_markup = None

            form_data = ["Submitted data :-\n"]
            for key in input_dict.keys():
                form_data.append("%s: %s" % (key, input_dict[key]))

            form_data = "\n".join(form_data)

            try:
                sql = (form_id, department_id, company_id)
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT form.title, form.company_id, form.department_id FROM form
                    WHERE form.id=%s AND form.department_id=%s AND form.company_id=%s LIMIT 1
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    form_details = cursor.fetchone()
                    try:
                        sql = (
                                form_details[0],
                                form_data,
                                form_details[1],
                                form_details[2],
                                name.get('id'),
                                'open'
                            )
                        cursor = yield momoko.Op(self.db.execute, """
                            INSERT INTO ticket (title, description, company_id, department_id, user_id, status)
                            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                            """, sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        if cursor.rowcount > 0:

                            ticket_id = cursor.fetchone()
                            if form_markup:
                                try:
                                    form_edata = []
                                    for key in input_dict.keys():
                                        for value in input_dict[key]:
                                            form_edata.append((key, value))
                                    form_edata = urlencode(form_edata).replace('+', '%20')
                                except:
                                    form_edata = None
                                upload_sql = [("""
                                    INSERT INTO form_data (data, markup, ticket_id) VALUES (%s, %s, %s)
                                """, (form_edata, form_markup, ticket_id))]
                            else:
                                upload_sql = []
                            if self.request.files:
                                for i in self.request.files.keys():
                                    f_name = self.request.files[i][0].get('filename')
                                    f_mime = self.request.files[i][0].get('content_type')
                                    f_body = self.request.files[i][0].get('body')
                                    if (f_name and f_mime and f_body):

                                        f_extn = f_name.split('.')

                                        if len(f_extn) == 1:
                                            f_extn = 'bin'
                                        else:
                                            f_extn = f_extn[-1][:4]

                                        f_path = "%s.%s" % (sha256("%s/%s" % (f_name, datetime.now())).hexdigest(), f_extn)
                                        upload_sql.append(("""
                                            INSERT INTO attachment (filename, filepath, content_type, ticket_id)
                                            VALUES (%s, %s, %s, %s)
                                        """, (f_name, f_path, f_mime, ticket_id)))

                                        filepath = os.path.join(self.settings["upload_path"], f_path)
                                        with open(filepath, 'wb') as f:
                                            f.write(f_body)
                            try:
                                cursor = yield momoko.Op(self.db.transaction, upload_sql)
                            except (psycopg2.Warning, psycopg2.Error) as error:
                                logging.error(str(error))
                                self.set_status(500)
                                self.write('Error/500')
                                self.finish()
                                return

                            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                self.write('/customer/tickets/view?ticket=%s' % ticket_id)
                                return

                            self.redirect('/customer/tickets/view?ticket=%s' % ticket_id)
                            return
                else:
                    self.set_status(400)
                    self.write('Error/400')
                    return

        try:
            company_id = self.get_argument('company')
            department_id = self.get_argument('department')
            title = self.get_argument('title')
            description = self.get_argument('description')

            upload = None
            if len(self.request.files.keys()):
                upload = self.request.files.get('upload')
                if upload is not None:
                    upload_name = upload[0]['filename']
                    upload_mime = upload[0]['content_type']
                    upload_data = upload[0]['body']
        except:
            self.set_status(400)
            self.flash('error_Please fill in all the fields!')
            self.redirect('/customer')
            return

        if not len(title) > 0:
            self.flash('error_Please enter a title.')
            self.redirect('/customer')
            return

        if not len(description) > 0:
            self.redirect('/customer')
            return

        try:
            sql = (title, description, company_id, department_id, name.get('id'), 'live')
            cursor = yield momoko.Op(self.db.execute, """
                INSERT INTO ticket (title, description, company_id, department_id, user_id, status)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, sql)
        except (psycopg2.Warning, psycopg2.Error) as error:
            logging.error(str(error))
            self.set_status(500)
            self.write('Error/500')
            self.finish()
            return
        else:
            if cursor.rowcount > 0:
                ticket_id = cursor.fetchone()
                if upload is not None:
                    try:
                        file_ext = upload_name.split('.')
                        if len(file_ext) == 1:
                            file_ext = 'bin'
                        else:
                            file_ext = file_ext[-1][:4]

                        upload_path = "%s.%s" % (sha256("%s/%s" % (upload_name, datetime.now())).hexdigest(), file_ext)
                        sql = (upload_name, upload_path, upload_mime, ticket_id)
                        cursor = yield momoko.Op(self.db.execute, """
                                INSERT INTO attachment (filename, filepath, content_type, ticket_id)
                                VALUES (%s, %s, %s, %s) RETURNING id
                            """, sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        if cursor.rowcount > 0:
                            filepath = os.path.join(self.settings["upload_path"], upload_path)
                            with open(filepath, 'wb') as f:
                                f.write(upload_data)

                self.redirect('/customer/tickets/view?ticket=%s' % ticket_id)
                return
            else:
                self.redirect('/customer')
                return
