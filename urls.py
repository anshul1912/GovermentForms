# coding: utf-8

from view import basesite
from view.company import head, agent, customer, chat
from view.fpublic import fpublic

ROUTES = [
    # basesite routes
    (r'/?', basesite.Home),

    (r'/auth/signup', basesite.CPSignupHandler),

    (r'/activate', basesite.CPActivationHandler),
    (r'/forgot', basesite.CPForgotPassword),

    (r'/auth/login', basesite.CPAuthHandler),

    (r'/auth/google', basesite.GoogleAuthHandler),
    (r'/auth/twitter', basesite.TwitterAuthHandler),
    (r'/auth/facebook', basesite.FacebookAuthHandler),

    (r'/auth/logout', basesite.LogoutHandler),

    (r'/company', head.Head),
    (r'/company/(.+?)', head.Head),

    (r'/agent', agent.Agent),
    (r'/agent/(.+?)', agent.Agent),

    (r'/customer', customer.Customer),
    (r'/customer/(.+?)', customer.Customer),
    (r'/wsticket/(\d+?)', chat.WSTicket),
    (r'/wsagent', chat.WSAgent),

    (r'/public', fpublic.Forum),
    (r'/public/(.+?)', fpublic.PTicket),

    (r'/pricing', basesite.PricingPage),
    (r'/pgtest', basesite.PGTest),
]
