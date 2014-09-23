# coding: utf-8

from .__init__ import *

class Agent(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, section=None):
        name = self.current_user

        if name.get('u_type') != 'Agent':
            self.write('403 - Forbidden')
            self.set_status(403)
            self.finish()
            return

        if section == 'profile':
            self.render2('company/agent/profile.html', **{'name': name})
            return

        if section == 'tickets':
            tickets = []
            try:
                sql = (name.get('id'), )
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT ticket.id, ticket.title, ticket.timestamp, ticket.status
                    FROM ticket WHERE ticket.status != 'close' AND ticket.status != 'live' AND ticket.department_id IN
                    (SELECT agent.department_id FROM agent WHERE agent.user_id=%s)
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

                self.render2('company/tickets/tickets-agent.html', **{'name': name, 'tickets': tickets})

            return

        if section == 'tickets/view':
            try:
                ticket_id = self.get_argument('ticket')
            except:
                self.redirect('/agent/tickets')
                return

            ## begin form viewer ##
            try:
                form_id = self.get_argument('form')
            except:
                form_id = None

            if form_id:
                sql = (form_id, ticket_id, name.get('id'))
                self.db.execute("""
                    SELECT form_data.data, form_data.markup, form_data.ticket_id FROM form_data
                    INNER JOIN ticket ON form_data.ticket_id=ticket.id
                    INNER JOIN department ON ticket.department_id=department.id
                    INNER JOIN agent ON department.id=agent.department_id
                    INNER JOIN auth_user ON agent.user_id=auth_user.id
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

                        self.render2('company/forms/form-viewer-agent.html', **{
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
            ## end form viewer ##

            sql = (ticket_id, name.get('id'))
            self.db.execute("""
                    SELECT * FROM ticket WHERE ticket.id=%s AND ticket.department_id IN
                    (SELECT agent.department_id FROM agent WHERE agent.user_id=%s) LIMIT 1
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
                    self.render2('company/tickets/ticket-view-agent.html', **{
                            'name': name,
                            'ticket': ticket,
                            'thread': ticket_thread,
                            'attachment': attachment,
                            'form_data': form_data,
                        })
                    return
                else:
                    self.redirect('/agent/tickets')
                    return

        if section == 'tickets/add':
            self.render2('company/tickets/tickets-agent-add.html', **{'name': name})
            return

        if section == 'forms':
            forms = []
            try:
                sql = (name.get('id'), )
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT form.id, form.title FROM form WHERE form.department_id IN
                    (SELECT agent.department_id FROM agent WHERE agent.user_id=%s)
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    forms = cursor.fetchall()

                self.render2('company/agent/forms.html', **{
                        'name': name,
                        'forms': forms
                    })
                return

        if section == 'forms/view':
            try:
                form_id = int(self.get_argument('form'))
            except:
                self.redirect('/agent/forms')
                return

            try:
                sql = (form_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT form.id, form.title, form.content FROM form WHERE form.id=%s AND form.department_id IN
                    (SELECT agent.department_id FROM agent WHERE agent.user_id=%s)
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
                    self.render2('company/forms/form-view-agent.html', **{
                            'name': name,
                            'form': form
                        })
                    return
                else:
                    self.redirect('/agent/forms')
                    return

        #self.redirect('/agent/tickets')
        tickets = []
        try:
            sql = (name.get('id'), )
            cursor = yield momoko.Op(self.db.execute, """
                SELECT ticket.id, ticket.title, ticket.timestamp, ticket.status
                FROM ticket WHERE ticket.status = 'live' AND ticket.department_id IN
                (SELECT agent.department_id FROM agent WHERE agent.user_id=%s)
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

            self.render2('company/tickets/tickets-agent-live.html', **{'name': name, 'tickets': tickets})

        #self.render2('company/agent/dashboard.html', **{'name': name})

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self, section=None):
        self.check_xsrf_cookie()

        name = self.current_user

        if name.get('u_type') != 'Agent':
            self.write('403 - Forbidden')
            self.set_status(403)
            self.finish()
            return

        if section == 'profile':
            try:
                agent = self.get_argument('agent')
                password = self.get_argument('password')
            except:
                self.redirect('/agent/profile')
                return

            if len(password) > 0:
                password = "%s%s" % (password, self.settings["password_salt"])
                password = sha256(password).hexdigest()

            try:
                if len(password) > 0:
                    sql = (agent, password, name.get('id'))
                    cursor = yield momoko.Op(self.db.execute, """
                        UPDATE auth_user SET name=%s, password=%s WHERE id=%s RETURNING name
                        """, sql)
                else:
                    sql = (agent, name.get('id'))
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
                    try:
                        sql = (agent, name.get('id'))
                        cursor = yield momoko.Op(self.db.execute, """
                            UPDATE agent SET name=%s WHERE user_id=%s RETURNING name
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
                            self.redirect('/agent/profile')
                            return
                        else:
                            self.write('Unspecified error')
                            return
                else:
                    self.write('Unspecified error')
                    self.set_status(500)
                    self.finish()
                    return

        if section == 'tickets/add':
            try:
                title = self.get_argument('t_title')
                description = self.get_argument('description')
                status = self.get_argument('status')
            except:
                self.redirect('/agent/tickets/add')
                return

            if not len(title) > 0:
                self.redirect('/agent/tickets/add')
                return

            try:
                sql = (title, description, status, name.get('id'), name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    INSERT INTO ticket (
                        title, description, status, department_id, company_id, user_id)
                        SELECT %s, %s, %s, department.id, company.id, %s FROM department
                        INNER JOIN agent ON department.id=agent.department_id
                        INNER JOIN company ON agent.company_id=company.id
                        WHERE agent.user_id=%s RETURNING id
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    self.redirect('/agent/tickets')
                    return
                else:
                    self.write('Unspecified error')
                    self.set_status(500)
                    return

        if section == 'tickets/view':
            try:
                ticket_id = self.get_argument('tid')
            except:
                self.redirect('/agent/tickets')
                return

            _notchat = False
            try:
                _notchat = self.get_argument('notchat')
            except:
                pass

            try:
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest' and _notchat is False:
                    try:
                        comment = self.get_argument('chat')
                    except:
                        self.redirect('/agent/tickets/view?ticket=%s' % ticket_id)
                        return

                    if not len(comment) > 0:
                        self.redirect('/agent/tickets/view?ticket=%s' % ticket_id)

                    sql_1 = (ticket_id, comment, name.get('id'))
                    cursor = yield momoko.Op(self.db.transaction, [
                        ("""
                            INSERT INTO ticket_thread (ticket_id, description, user_id)
                            SELECT %s, %s, agent.user_id FROM department
                            INNER JOIN agent ON department.id=agent.department_id
                            INNER JOIN company ON agent.company_id=company.id
                            WHERE agent.user_id=%s
                        """, sql_1)
                    ])
                else:
                    try:
                        comment = self.get_argument('comment')
                        status = self.get_argument('status')
                    except:
                        self.write(self.request.arguments)
                        # self.redirect('/agent/tickets/view?ticket=%s' % ticket_id)
                        return

                    if not len(comment) > 0:
                        self.redirect('/agent/tickets/view?ticket=%s' % ticket_id)

                    sql_1 = (ticket_id, comment, name.get('id'))
                    sql_2 = (status, ticket_id)
                    cursor = yield momoko.Op(self.db.transaction, [
                        ("""
                            INSERT INTO ticket_thread (ticket_id, description, user_id)
                            SELECT %s, %s, agent.user_id FROM department
                            INNER JOIN agent ON department.id=agent.department_id
                            INNER JOIN company ON agent.company_id=company.id
                            WHERE agent.user_id=%s
                        """, sql_1),
                        ("""
                            UPDATE ticket SET status = %s
                            WHERE id=%s
                        """, sql_2)
                    ])
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    self.set_status(200)
                    self.finish()
                    return

                self.redirect('/agent/tickets/view?ticket=%s' % ticket_id)
                return

        if section == 'forms/view':
            input_dict = self.request.arguments

            input_dict.pop('_xsrf', None)
            input_dict.pop('form', None)
            form_id = input_dict.pop('fid', [None])[0]

            if not form_id:
                self.set_status(400)
                self.write('Error/400')
                return

            form_data = ["Submitted data :-\n"]
            for key in input_dict.keys():
                form_data.append("%s: %s" % (key, input_dict[key]))

            form_data = "\n".join(form_data)

            try:
                sql = (form_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT form.title, form.company_id, form.department_id FROM form WHERE form.id=%s AND form.department_id IN
                    (SELECT agent.department_id FROM agent WHERE agent.user_id=%s) LIMIT 1
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
                            self.redirect('/agent/tickets/view?ticket=%s' % ticket_id)
                            return
                else:
                    self.set_status(400)
                    self.write('Error/400')
                    return
