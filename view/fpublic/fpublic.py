# coding: utf-8

from .__init__ import *

class Forum(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        name = self.current_user

        companies = None
        try:
            companies = self.get_argument('companies')
        except:
            pass

        if companies:
            try: # TODO: Paginate this as well
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT id, name, description, logo FROM company
                """)
            except (psycopg2.Warning, psycopg2.Error) as error:
                logging.error(str(error))
                self.set_status(500)
                self.write('Error/500')
                self.finish()
                return
            else:
                results = []
                for i in cursor.fetchall():
                    results.append({
                        'id': i[0],
                        'name': i[1],
                        'description': i[2],
                        'logo': i[3]
                    })
                self.write(json.dumps(results))
                return

        offset = datetime.now()
        try:
            offset = datetime.strptime(self.get_argument('ts'), '%Y-%m-%d %H:%M:%S.%f')
        except:
            pass

        o_json = False
        try:
            o_json = self.get_argument('json')
        except:
            pass

        f_company = None
        try:
            f_company = self.get_argument('company')
        except:
            pass

        f_results = 5
        try:
            f_results = self.get_argument('r')
        except:
            pass

        try:
            if not f_company:
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT ticket.title, forum.message, company.name, auth_user.name, forum.timestamp, ticket.id, auth_user.email
                    FROM forum INNER JOIN ticket ON forum.ticket_id=ticket.id
                    INNER JOIN auth_user ON forum.user_id=auth_user.id
                    INNER JOIN company ON ticket.company_id=company.id
                    WHERE forum.timestamp < %s
                    ORDER BY forum.timestamp DESC LIMIT %s
                    """, (offset, f_results))
            else:
                cursor = yield momoko.Op(self.db.execute, """
                    SELECT ticket.title, forum.message, company.name, auth_user.name, forum.timestamp, ticket.id, auth_user.email
                    FROM forum INNER JOIN ticket ON forum.ticket_id=ticket.id
                    INNER JOIN auth_user ON forum.user_id=auth_user.id
                    INNER JOIN company ON ticket.company_id=company.id
                    WHERE forum.timestamp < %s AND company.name=%s
                    ORDER BY forum.timestamp DESC LIMIT %s
                    """, (offset, f_company, f_results))
        except (psycopg2.Warning, psycopg2.Error) as error:
            logging.error(str(error))
            self.set_status(500)
            self.write('Error/500')
            self.finish()
            return
        else:
            fdata = cursor.fetchall()

            for i in range(len(fdata)):
                fdata[i] = list(fdata[i])

            for i in range(len(fdata)):
                if len(fdata[i][1]) > 100:
                    fdata[i][1] = fdata[i][1][:100] + '...'
                else:
                    fdata[i][1] = fdata[i][1][:100]
                fdata[i][4] = fdata[i][4].strftime('%Y-%m-%d %H:%M:%S.%f')
                fdata[i][3] = fdata[i][3] or fdata[i][6]

            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest' or o_json:
                self.write(json.dumps(fdata))
                return

            self.render2('fpublic/forum.html', **{'name': name, 'fdata': fdata})

class PTicket(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, ticket_id=None):
        name = self.current_user
        fdata = []

        try:
            ticket_id = int(ticket_id)
        except:
            self.set_status(400)
            self.write("Error/400 - Ticket id must be an integer.")
            return

        try:
            cursor = yield momoko.Op(self.db.execute, """
                SELECT ticket.title, ticket.description, forum.message, forum.timestamp,
                auth_user.name, auth_user.avatar, ticket.timestamp, auth_user.email
                FROM forum INNER JOIN ticket ON forum.ticket_id=ticket.id
                INNER JOIN auth_user ON ticket.user_id=auth_user.id
                WHERE ticket.id=%s LIMIT 1
                """, (ticket_id, ))
        except (psycopg2.Warning, psycopg2.Error) as error:
            logging.error(str(error))
            self.set_status(500)
            self.write('Error/500')
            self.finish()
            return
        else:
            if cursor.rowcount > 0:
                fdata = cursor.fetchone()
                fdata = list(fdata)
                fdata[4] = fdata[4] or fdata[7]
            else:
                self.set_status(404)
                self.write("Error/404 - resource not found")
                return

    	self.render2('fpublic/fpublic.html', **{'name': name, 'fdata': fdata})
