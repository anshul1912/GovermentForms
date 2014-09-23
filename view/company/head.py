# coding: utf-8

from .__init__ import *

class Head(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, section=None):
        name = self.current_user

        if name.get('u_type') != 'Company':
            self.write('403 - Forbidden')
            self.set_status(403)
            self.finish()
            return

        if section == 'profile':
            company = []
            try:
                sql = (name.get('id', None), )
                cursor = yield momoko.Op(self.db.execute,
                    "SELECT name, description FROM company WHERE user_id=%s LIMIT 1", sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    company = cursor.fetchone()

            self.render2('company/head/profile.html', **{'name': name, 'company': company})
            self.finish()
            return

        if section == 'departments':
            departments = []
            try:
                sql = (name.get('id', None), )
                cursor = yield momoko.Op(self.db.execute, """
                        SELECT department.name, department.description, department.id FROM department
                        INNER JOIN company ON department.company_id=company.id
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    departments = cursor.fetchall()

            self.render2('company/head/departments.html', **{'name': name, 'departments': departments})
            self.finish()
            return

        if section == 'departments/add':
            self.render2('company/head/departments-add.html', **{'name': name})
            self.finish()
            return

        if section == 'departments/edit':
            department = []
            department_id = self.get_argument('department')
            try:
                department_id = int(department_id)
            except:
                self.redirect('/company/departments')
                return
            try:
                sql = (name.get('id', None), department_id)
                cursor = yield momoko.Op(self.db.execute, """
                        SELECT department.name, department.description, department.id FROM department
                        INNER JOIN company ON department.company_id=company.id
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s AND department.id=%s LIMIT 1
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    department = cursor.fetchone()
                else:
                    self.redirect('/company/departments/add')
                    return

            self.render2('company/head/departments-add.html', **{'name': name, 'department': department})
            self.finish()
            return

        if section == 'agents':
            agents = []
            try:
                sql = (name.get('id', None), )
                cursor = yield momoko.Op(self.db.execute, """
                        SELECT agent.name, department.name, agent.user_id FROM agent
                        INNER JOIN department ON agent.department_id=department.id
                        INNER JOIN company ON agent.company_id=company.id
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    agents = cursor.fetchall()

            self.render2('company/head/agents.html', **{'name': name, 'agents': agents})
            self.finish()
            return

        if section == 'agents/add':
            agent = []
            departments = []
            try:
                sql = (name.get('id', None), )
                cursor = yield momoko.Op(self.db.execute, """
                        SELECT department.id, department.name FROM department
                        INNER JOIN company ON department.company_id=company.id
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    departments = cursor.fetchall()
                else:
                    self.redirect('/company/departments/add')
                    return

            self.render2('company/head/agents-add.html', **{'name': name, 'departments': departments, 'agent': agent})
            self.finish()
            return

        if section == 'agents/edit':
            agent_id = self.get_argument('agent')
            try:
                agent_id = int(agent_id)
            except:
                self.redirect('/company/agents')
                return

            agent = []
            departments = []

            # WARNING:momoko:Execute: no connection available, operation queued. <-- wtf? O_o
            sql = (name.get('id', None), )
            self.db.execute("""
                                SELECT department.id, department.name FROM department
                                INNER JOIN company ON department.company_id=company.id
                                INNER JOIN auth_user ON company.user_id=auth_user.id
                                WHERE auth_user.id=%s
                            """, sql, callback=(yield gen.Callback('q1')))

            sql = (name.get('id', None), agent_id)
            self.db.execute("""
                                SELECT agent.name, agent.email, department.id, agent.user_id FROM agent
                                INNER JOIN department ON agent.department_id=department.id
                                INNER JOIN company ON agent.company_id=company.id
                                INNER JOIN auth_user ON company.user_id=auth_user.id
                                WHERE auth_user.id=%s AND agent.user_id=%s LIMIT 1
                            """, sql, callback=(yield gen.Callback('q2')))

            try:
                cursor_q1, cursor_q2 = yield momoko.WaitAllOps(('q1', 'q2'))
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor_q1.rowcount > 0:
                    departments = cursor_q1.fetchall()
                else:
                    self.redirect('/company/departments/add')
                    return
                if cursor_q2.rowcount > 0:
                    agent = cursor_q2.fetchone()
                else:
                    self.redirect('/company/agents/add')
                    return
            self.render2('company/head/agents-add.html', **{'name': name, 'departments': departments, 'agent': agent})
            self.finish()
            return

        if section == 'forms':
            forms = []
            try:
                sql = (name.get('id'), )
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT form.id, form.title FROM form WHERE form.company_id IN
                    (SELECT company.id FROM company
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s LIMIT 1)
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

                self.render2('company/head/forms.html', **{
                        'name': name,
                        'forms': forms
                    })
                return

        if section == 'forms/add':
            departments = []
            try:
                sql = (name.get('id', None), )
                cursor = yield momoko.Op(self.db.execute, """
                        SELECT department.id, department.name FROM department
                        INNER JOIN company ON department.company_id=company.id
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    departments = cursor.fetchall()

                self.render2('/company/head/forms-add.html', **{'name': name, 'departments': departments})
                return

        if section == 'forms/view':
            try:
                form_id = int(self.get_argument('form'))
            except:
                self.redirect('/company/forms')
                return

            try:
                sql = (form_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT form.id, form.title, form.content, department.id, department.name, company.id, company.name
                    FROM form INNER JOIN department ON form.department_id=department.id
                    INNER JOIN company ON department.company_id=company.id
                    INNER JOIN auth_user ON company.user_id=auth_user.id
                    WHERE form.id=%s AND auth_user.id=%s LIMIT 1
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
                    self.render2('company/forms/form-view-head.html', **{
                            'name': name,
                            'form': form
                        })
                    return
                else:
                    self.set_status(404)
                    return

        if section == 'packages':
            self.render2('company/head/packages.html', **{'name': name})
            self.finish()
            return

        self.db.execute("""
                            SELECT count(agent.id) FROM agent
                            INNER JOIN company ON agent.company_id=company.id
                            INNER JOIN auth_user ON company.user_id=auth_user.id
                            WHERE auth_user.id=%s
                        """, (name.get('id'), ), callback=(yield gen.Callback('q1')))

        self.db.execute("""
                            SELECT count(department.id) FROM department
                            INNER JOIN company ON department.company_id=company.id
                            INNER JOIN auth_user ON company.user_id=auth_user.id
                            WHERE auth_user.id=%s
                        """, (name.get('id'), ), callback=(yield gen.Callback('q2')))

        agents = 0
        departments = 0

        try:
            cursor_q1, cursor_q2 = yield momoko.WaitAllOps(('q1', 'q2'))
        except (psycopg2.Warning, psycopg2.Error) as error:
            logging.error(str(error))
            self.set_status(500)
            self.write('Error/500')
            self.finish()
            return
        else:
            if cursor_q1.rowcount > 0:
                agents = cursor_q1.fetchone()[0]
            if cursor_q2.rowcount > 0:
                departments = cursor_q2.fetchone()[0]

        self.render2('company/head/dashboard.html', **{'name': name, 'agents': agents, 'departments': departments})

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self, section=None):
        self.check_xsrf_cookie()

        name = self.current_user

        if name.get('u_type') != 'Company':
            self.write('403 - Forbidden')
            self.set_status(403)
            self.finish()
            return

        if section == 'profile':
            try:
                company = self.get_argument('company')
                description = self.get_argument('description')
            except:
                self.redirect('/company/profile')
                return

            if not len(company) > 0:
                self.redirect('/company/profile')
                return

            upload = None
            try:
                if len(self.request.files.keys()):
                    upload = self.request.files.get('upload')
                    if upload is not None:
                        upload_name = upload[0]['filename']
                        upload_mime = upload[0]['content_type']
                        upload_data = upload[0]['body']
            except:
                pass # No new logo

            try:
                sql = (company, description, name.get('id'), name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    INSERT INTO company (name, description, user_id)
                    SELECT %s, %s, %s WHERE NOT EXISTS
                    (SELECT id FROM company WHERE user_id=%s) RETURNING id
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if not cursor.rowcount > 0:
                    try:
                        sql = (company, description, name.get('id'))
                        if not upload:
                            cursor = yield momoko.Op(self.db.execute, """
                                UPDATE company SET
                                name = %s,
                                description = %s
                                WHERE user_id = %s
                                """, sql)
                        else:
                            file_ext = upload_name.split('.')
                            if len(file_ext) == 1:
                                file_ext = 'bin'
                            else:
                                file_ext = file_ext[-1][:4]

                            logo = "%s.%s" % (sha256("%s/%s" % (upload_name, datetime.now())).hexdigest(), file_ext)
                            with open(os.path.join(self.settings["upload_path"], logo), 'wb') as f:
                                f.write(upload_data)

                            sql = (company, description, logo, name.get('id'))
                            cursor = yield momoko.Op(self.db.execute, """
                                UPDATE company SET
                                name = %s,
                                description = %s, logo=%s
                                WHERE user_id = %s
                                """, sql)

                            user_key = self.get_secure_cookie("u_key")
                            self.mc.hset(user_key, 'c_logo', logo)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        self.redirect('/company/profile')
                        return
                else:
                    self.redirect('/company/profile')
                    return

        if section == 'departments':
            try:
                action = self.get_argument('action')
                department_id = int(self.get_argument('department_id'))
            except:
                self.redirect('/company/departments')
                return

            try:
                sql = (department_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    DELETE FROM department WHERE
                    department.id = %s AND department.company_id IN
                    (SELECT company.id FROM company
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s LIMIT 1);
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                self.redirect('/company/departments')
                return

        if section == 'agents':
            try:
                action = self.get_argument('action')
                agent_id = int(self.get_argument('agent_id'))
            except:
                self.redirect('/company/agents')
                return

            try:
                sql = (agent_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    DELETE FROM agent WHERE
                    agent.user_id = %s AND agent.company_id IN
                    (SELECT company.id FROM company
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s LIMIT 1) RETURNING user_id;
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
                        agent_id = cursor.fetchone()[0]
                        sql = (agent_id, agent_id)
                        cursor = yield momoko.Op(self.db.execute, """
                            DELETE FROM auth_user WHERE auth_user.id=%s AND NOT EXISTS
                            (SELECT 1 FROM agent WHERE agent.user_id=%s LIMIT 1)
                            """, sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        self.redirect('/company/agents')
                        return

        if section == 'forms':
            try:
                action = self.get_argument('action')
                form_id = int(self.get_argument('fid'))
            except:
                self.redirect('/company/forms')
                return

            try:
                sql = (form_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    DELETE FROM form WHERE
                    form.id = %s AND form.company_id IN
                    (SELECT company.id FROM company
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s LIMIT 1);
                    """, sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                self.redirect('/company/forms')
                return

        if section == 'departments/add' or section == 'departments/edit':
            try:
                department = self.get_argument('department')
                description = self.get_argument('description')
                if section == 'departments/edit':
                    department_id = int(self.get_argument('department_id'))
            except:
                self.redirect('/company/departments/add')
                return

            if not len(department) > 0:
                self.redirect('/company/departments/add')
                return

            try:
                sql = (department, description, name.get('id'))

                if section == 'departments/edit':
                    sql = sql + (department_id, )
                    cursor = yield momoko.Op(self.db.execute, """
                        UPDATE department SET
                        name = %s, description = %s, company_id = subquery.id
                        FROM (SELECT company.id FROM company
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s) AS subquery
                        WHERE department.id = %s""", sql)

                elif section == 'departments/add':
                    cursor = yield momoko.Op(self.db.execute, """
                        INSERT INTO department (name, description, company_id)
                        SELECT %s, %s, company.id FROM company
                        INNER JOIN auth_user ON company.user_id=auth_user.id
                        WHERE auth_user.id=%s LIMIT 1 RETURNING department.id""", sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    self.redirect('/company/departments')
                    return
                else:
                    self.write('Unspecified error')
                    return

        if section == 'agents/add': # or section == 'agents/edit':
            try:
                agent = self.get_argument('agent')
                email = self.get_argument('agent_email')
                password = self.get_argument('password')
                department_id = int(self.get_argument('department'))
                agent_type = 'Junior' # beat Kunal for this :s
            except:
                self.redirect('/company/agents/add')
                return

            if not len(email) > 0:
                self.redirect('/company/agents/add')
                return

            if not len(password) > 0:
                self.redirect('/company/agents/add')
                return

            password = "%s%s" % (password, self.settings["password_salt"])
            password = sha256(password).hexdigest()

            try:
                cursor = yield momoko.Op(self.db.execute, """
                    INSERT INTO auth_user (name, email, password, u_type)
                    VALUES (%s, %s, %s, 'Agent') RETURNING id
                    """, (agent, email, password))

            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    try:
                        user_id = cursor.fetchone()[0]
                        sql = (agent, email, department_id, user_id, agent_type, name.get('id'))
                        cursor = yield momoko.Op(self.db.execute, """
                            INSERT INTO agent (name, email, department_id, company_id, user_id, type)
                            SELECT %s, %s, %s, company.id, %s, %s FROM company
                            INNER JOIN auth_user ON company.user_id=auth_user.id
                            WHERE auth_user.id=%s
                            """, sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        if cursor.rowcount > 0:
                            self.redirect('/company/agents')
                            return
                        else:
                            self.write('Unspecified error')
                            return

        if section == 'agents/edit':
            try:
                agent = self.get_argument('agent')
                email = self.get_argument('agent_email')
                password = self.get_argument('password')
                department = int(self.get_argument('department'))
                agent_id = int(self.get_argument('agent_id'))
                agent_type = 'Junior'
            except:
                self.redirect('/company/agents')
                return

            if not len(email) > 0:
                self.redirect('/company/agents/edit?agent=%s' % agent_id)
                return

            if len(password) > 0:
                password = "%s%s" % (password, self.settings["password_salt"])
                password = sha256(password).hexdigest()

            try:
                if len(password) > 0:
                    sql = (agent, password, email, agent_id, email)
                    cursor = yield momoko.Op(self.db.execute, """
                        UPDATE auth_user SET
                        name = %s, password = %s, email = %s
                        WHERE auth_user.id = %s AND auth_user.email IN
                        (SELECT email FROM auth_user WHERE email=%s)
                        RETURNING id""", sql)
                else:
                    sql = (agent, email, agent_id, email)
                    cursor = yield momoko.Op(self.db.execute, """
                        UPDATE auth_user SET
                        name = %s, email = %s
                        WHERE auth_user.id = %s AND auth_user.email IN
                        (SELECT email FROM auth_user WHERE email=%s)
                        RETURNING id""", sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    agent_id = cursor.fetchone()[0]
                    try:
                        sql = (agent, email, department, agent_type, name.get('id'), agent_id)
                        cursor = yield momoko.Op(self.db.execute, """
                            UPDATE agent SET
                            name = %s, email = %s, department_id=%s, type=%s, company_id = subquery.id
                            FROM (SELECT company.id FROM company
                            INNER JOIN auth_user ON company.user_id=auth_user.id
                            WHERE auth_user.id=%s) AS subquery
                            WHERE agent.user_id = %s""", sql)
                    except (psycopg2.Warning, psycopg2.Error) as error:
                        logging.error(str(error))
                        self.set_status(500)
                        self.write('Error/500')
                        self.finish()
                        return
                    else:
                        if cursor.rowcount > 0:
                            self.redirect('/company/agents')
                            return
                        else:
                            self.write('Unspecified error')
                            return
                else:
                    self.redirect('/company/agents/edit?agent=%s' % agent_id)
                    return

        if section == 'forms/add':
            try:
                title = self.get_argument('title')
                content = self.get_argument('content')
                department_id = int(self.get_argument('department_id'))
            except:
                self.set_status(400)
                self.write('Error/400')
                return

            if not len(title) > 0:
                self.set_status(400)
                self.write('Error/400 -- title is required')
                return

            if not len(content) > 0:
                self.set_status(400)
                self.write('Error/400 -- content is required')
                return

            try:
                c = Cleaner(
                        scripts=True,
                        javascript=True,
                        comments=True,
                        style=False,
                        links=True,
                        meta=True,
                        page_structure=True,
                        processing_instructions=True,
                        embedded=True,
                        frames=True,
                        forms=False,
                        annoying_tags=True,
                        remove_unknown_tags=True,
                        add_nofollow=True
                    )
                content = c.clean_html(content)
            except:
                self.set_status(400)
                self.redirect('/company/forms/add')
                return

            try:
                sql = (title, content, department_id, name.get('id'))
                cursor = yield momoko.Op(self.db.execute, """
                    INSERT INTO form (title, content, department_id, company_id)
                    SELECT %s, %s, %s, company.id FROM company
                    INNER JOIN auth_user ON company.user_id=auth_user.id
                    WHERE auth_user.id=%s RETURNING id""", sql)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                if cursor.rowcount > 0:
                    self.set_status(200)
                    return
                else:
                    self.set_status(500)
                    self.write('Error/500')
                    return