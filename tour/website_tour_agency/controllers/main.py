# See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
from odoo import fields
from werkzeug import urls
import ast,math
import werkzeug.utils
from odoo.tools.misc import get_lang, format_date
from odoo import http
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class QueryURL(object):
    def __init__(self, path="", **args):
        self.path = path
        self.args = args

    def __call__(self, path=None, **kw):
        if not path:
            path = self.path
        for k, v in self.args.items():
            kw.setdefault(k, v)
        lst = []
        for k, v in kw.items():
            if v:
                if isinstance(v, list) or isinstance(v, set):
                    lst.append(werkzeug.url_encode([(k, i) for i in v]))
                else:
                    lst.append(werkzeug.url_encode([(k, v)]))
        if lst:
            path += "?" + "&".join(lst)
        return path


class WebsiteHomepage(Website):
    @http.route()
    def index(self, **kw):
        domain = [("website_published", "=", True)]
        packages = request.env["package.category"].search(domain)
        testimonials = (
            request.env["testimonial.testimonial"]
            .sudo()
            .search(domain, order="sequence asc")
        )
        return request.render(
            "website.homepage", {"testimonials": testimonials, "packages": packages}
        )


class WebsiteTours(http.Controller):
    @http.route(["/packages"], type="http", auth="public", website=True)
    def packages(self, search="", page=0, **kwargs):
        attrib_list = request.httprequest.args.getlist("categories")
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]

        attrib_ids = [set(v) for v in attrib_values]

        attrib_set1 = list(attrib_ids)
        attrib_set = [list(i)[0] for i in attrib_set1]
        keep = QueryURL("/")
        domain = [
            ("state", "=", "confirm"),
            ("website_published", "=", True),
        ]
        package_categ = request.env["package.category"].search(
            [("website_published", "=", True)]
        )
        if search:
            kwargs["search"] = search
            search = kwargs["search"]
            domain += [("name", "ilike", search)]
        if attrib_set:
            domain += [("category_id", "in", attrib_set)]
        packages = request.env["sale.order.template"].search(
            domain, order="write_date desc"
        )
        return request.render(
            "website_tour_agency.packages",
            {
                "keep": keep,
                "search": search,
                "package_categs": package_categ,
                "categs_selected": attrib_set,
                "packages": packages,
            },
        )


    @http.route(
        ["""/hotel/details/<int:partner_id>"""],
        type="http",
        auth="public",
        website=True,
    )
    def hotel_details_view(self, partner_id=0, **post):
        values = {
            "countries": request.env["res.country"].sudo().search([]),
            "company": request.env["res.company"].sudo().search([]),
        }
        if partner_id:
            hotel = (
                request.env["res.partner"]
                .sudo()
                .search(
                    [
                        ("id", "=", partner_id),
                        ("registration_type", "=", "hotel"),
                        ("is_hotel", "=", True),
                        ("website_visible", "=", True),
                    ]
                )
            )
            if hotel:
                values.update({"template": hotel})
        return request.render("website_tour_agency.hotel_details_page", values)

    @http.route(
        ["/hotel/details/<int:partner_id>/inquiry"],
        type="http",
        auth="public",
        website=True,
    )
    def hotel_inquiry(self, partner_id=0, **post):
        values = {
            "countries": request.env["res.country"].sudo().search([]),
            "company": request.env["res.company"].sudo().search([]),
        }
        if partner_id:
            hotel = (
                request.env["res.partner"]
                .sudo()
                .search(
                    [
                        ("id", "=", partner_id),
                        ("registration_type", "=", "hotel"),
                        ("is_hotel", "=", True),
                        ("website_visible", "=", True),
                    ]
                )
            )
            if hotel:
                values.update({"hotel": hotel})
        return request.render("website_tour_agency.hotel_inquiry", values)

    @http.route(
        ["/get_package_data"],
        type="json",
        auth="public",
        website=True,
    )
    def get_package_data(self,**post):
        package = request.env['sale.order.template'].sudo().browse(int(post.get('package')))
        try:
            tarvell_date = datetime.strptime(post.get('date'), get_lang(request.env).date_format).date()
        except:
            tarvell_date = datetime.strptime(post.get('date'), "%Y-%m-%d").date()
        total_rate = 0.0
        if post.get('group_package') != ' ':
            group_line = request.env['group.costing.line'].sudo().browse(int(post.get('group_package')))
            total_rate = package.get_group_cost_package_price(tarvell_date,group_line)
        rate = package.get_updated_package_price(tarvell_date)
        return_date = (tarvell_date + timedelta(days=package.fixed_tour_days))
        return {'rate': rate or 0.0,
                'return_date': return_date,
                'total_rate': total_rate}

    @http.route(
        ["/group_costing"],
        type="json",
        auth="public",
        website=True,
    )
    def get_group_costing(self,**post):
        package = request.env['sale.order.template'].sudo().browse(int(post.get('package')))
        data_dict = {'rate': 0.0,
                    'adults': 0,
                    'children': 0}
        if post.get('group_package') != ' ':
            group_line = request.env['group.costing.line'].sudo().browse(int(post.get('group_package')))
            data_dict = {
                    'adults': group_line.number_of_adult or 0,
                    'children': group_line.number_of_children or 0}
            tarvell_date = False
            if post.get('date'):
                date_post = post.get('date')
                try:
                    tarvell_date = datetime.strptime(date_post, get_lang(request.env).date_format).date()
                except:
                    tarvell_date = datetime.strptime(date_post,'%Y-%m-%d')
            rate = package.get_group_cost_package_price(tarvell_date,group_line)
            data_dict.update({'rate': rate or 0.0})
        return data_dict

    @http.route(
        ["/save_traveller"],
        type="json",
        auth="public",
        website=True,
    )
    def save_traveller(self,**post):
        # img_data = post.get('img_data')
        # file_name = post.get('file_name')
#         if post.get('birth_date'):
            # birth_date = datetime.strptime(post.get('birth_date'), get_lang(request.env).date_format).date()
        # post.pop('img_data')
        # post.pop('file_name')
        traveller = request.env['travellers.list'].sudo().create(post)
        # if file_name and img_data:
        #     files = file_name.split(',')
        #     imgs = img_data.split(',')
        #     count = 0
        #     for file in files:
        #         vals = {'name': file,
        #             'datas': imgs[count],
        #             'res_model': 'travellers.list',
        #             'res_id': traveller.id,
        #             'type': 'binary'}
        #         attachment_rec = request.env['ir.attachment'].sudo().create(vals)
        #         count = count + 1
        data = {'tarvell_id': traveller.id,
                'tarvell_name': traveller.name,
                'birthdate': traveller.age,
                'gender': traveller.gender,
                'identity_type': traveller.identity_type,
                'identity_number': traveller.identity_number}
        table_row = '''<tr data-traveller_id='''+ str(traveller.id)+ '''>
            <input type="hidden" class="traveller_rec_'''+str(traveller.id)+'''" value="'''+ str(traveller.id) +'''"/>
            <td>'''+ traveller.name + '''</td>
            <td>''' + str(traveller.age) + '''</td>
            <td>''' + traveller.gender + '''</td>
            <td class="delete_td" data-traveller_id='''+ str(traveller.id)+ '''><i class="fa fa-trash delete_rec"/></td>
            </tr>'''


        # table_row = '''<tr data-traveller_id='''+ str(traveller.id)+ '''>
        #     <input type="hidden" class="traveller_rec_'''+str(traveller.id)+'''" value="'''+ str(traveller.id) +'''"/>
        #     <td>'''+ traveller.name + '''</td>
        #     <td>''' + str(traveller.age) + '''</td>
        #     <td>''' + traveller.gender + '''</td>
        #     <td>''' + traveller.identity_type + '''</td>
        #     <td>'''+ traveller.identity_number+ '''</td>
        #     <td class="delete_td" data-traveller_id='''+ str(traveller.id)+ '''><i class="fa fa-trash delete_rec"/></td>
        #     </tr>'''
        return table_row

    @http.route(
        ["/delete_traveller"],
        type="json",
        auth="public",
        website=True,
    )
    def delete_traveller(self,**post):
        traveller = request.env['travellers.list'].sudo().browse(int(post.get('tarvel_id')))
        if traveller:
            traveller.unlink()
            return True
        else:
            return False

    @http.route(
        ["/package/details/<model('sale.order.template'):order>"],
        type="http",
        auth="public",
        website=True,
    )
    def package_details_view(self, order, **post):
        if order and order.website_published:
            values = {
                "template": order,
                "countries": request.env["res.country"].sudo().search([]),
                "company": request.env["res.company"].sudo().search([]),
            }
            return request.render("website_tour_agency.package_details", values)
        else:
            return request.redirect('/packages')

    @http.route(
        ["/package/details/<model('sale.order.template'):order>/inquiry"],
        type="http",
        auth="public",
        website=True,
    )
    def package_inquiry(self, order, **post):
        values = {
            "template": order,
            "countries": request.env["res.country"].sudo().search([]),
            "company": request.env["res.company"].sudo().search([]),
        }
        return request.render("website_tour_agency.package_inquiry", values)

    @http.route(
        ["/package/details/<model('sale.order.template'):order>/book"],
        type="http",
        auth="public",
        website=True,
    )
    def package_book(self, order, **post):
        values = {
            "template": order,
            "countries": request.env["res.country"].sudo().search([]),
            "company": request.env["res.company"].sudo().search([]),
        }
        return request.render("website_tour_agency.package_booking", values)

    @http.route(["/visa/inquiry"], type="http", auth="public", website=True)
    def visa_inquiry(self, **post):
        domain = [("type_travel_product", "=", "visa")]
        visa_list = request.env["product.product"].sudo().search(domain)
        values = {
            "visas": visa_list,
            "countries": request.env["res.country"].sudo().search([]),
            "company": request.env["res.company"].sudo().search([]),
        }
        return request.render("website_tour_agency.visa_inquiry", values)

    @http.route(["/contactus_thanks_travel"], type="http", auth="public", website=True)
    def contact_us(self, **post):
        return request.render("website_tour_agency.contactus_thanks_travel")

    @http.route(["/visa"], type="http", auth="public", website=True)
    def get_visa(self, **post):
        return request.render("website_tour_agency.visa")

    @http.route(["/transportation"], type="http", auth="public", website=True)
    def get_trasportation(self, **post):
        val = {
            "countries": request.env["res.country"].sudo().search([]),
        }
        return request.render("website_tour_agency.transportation", val)

    @http.route(
        ["/book_package"], type="http", auth="public", website=True, csrf=False
    )
    def register_for_package(self, **post):
        if "date_of_arrival" in post and post.get("date_of_arrival"):
            start_dt = datetime.strptime(post.get("date_of_arrival"), "%Y-%m-%d").date()
            post.update({"date_of_arrival": start_dt})
        if "date_of_return" in post and post.get("date_of_return"):
            end_dt = datetime.strptime(post.get("date_of_return"), "%Y-%m-%d").date()
            post.update({"date_of_return": end_dt})
        package = request.env['sale.order.template'].sudo().browse(int(post.get('package_id')))
        group_costing = False
        if post.get('group_costing_id'):
            group_costing = request.env['group.costing.line'].sudo().browse(int(post.get('group_costing_id')))
        post.pop('group_costing_id')
        if package:
            post.update({'type_of_package': package.type_of_package,
                         'tour_type': package.package_type})
            if package and package.type_of_package == 'specific':
                post.update({'date_of_arrival': package.arrival_date,
                         'date_of_return': package.return_date})
        if post.get('travellers_ids'):
            travellers_ids = ast.literal_eval(post.get('travellers_ids'))
            if isinstance(travellers_ids, int):
                travellers_ids = [travellers_ids]
            else:
                travellers_ids = list(travellers_ids)
        
        post.pop("travellers_ids")
        # Lead Generation
        lead = request.env["crm.lead"].sudo().create(post)
        # Create or Link Partner from Lead
        partner = lead._create_customer()
        lead.convert_opportunity(partner)
        lead.action_set_won()
        # Create Registration
        vals = {'is_registration': True,
                'partner_id': partner.id,
                'sale_order_template_id': package.id,
                'group_costing_id': group_costing.id,
                'tour_begin_date': lead.date_of_arrival,
                'tour_end_date':lead.date_of_return,
                'adults':lead.adult,
                'children':lead.children,
                'infants':lead.infants,
                'passenger_ids': [(6,0, travellers_ids)] or [],
        }
        order = request.env['sale.order'].sudo().create(vals)
        order.onchange_sale_order_template_id()
        order.get_group_cost()
        lead.update({
            'order_id':order.id
        })
        template = request.env.ref("website_tour_agency.registration_notification")
        template.sudo().send_mail(lead.id, force_send=True)
        return request.render("website_tour_agency.package_thanks_travel")
        #Redirect to Payment link
        # default_data = request.env['payment.link.wizard']\
        #         .with_context(
        #             active_ids=order.id,
        #             active_id=order.id,
        #             active_model='sale.order')\
        #         .default_get([
        #             'res_model',
        #             'res_id',
        #         ])
        # return_wiz = request.env['payment.link.wizard'].sudo().with_context(
        #     active_ids=order.id,active_id=order.id, active_model='sale.order').create(default_data)
        # record = request.env[return_wiz.res_model].browse(return_wiz.res_id)
        # link = ('%s/payment/pay?reference=%s&amount=%s&currency_id=%s'
        #                             '&partner_id=%s&order_id=%s&company_id=%s&access_token=%s') % (
        #                                 record.get_base_url(),
        #                                 urls.url_quote_plus(return_wiz.description),
        #                                 return_wiz.amount,
        #                                 return_wiz.currency_id.id,
        #                                 return_wiz.partner_id.id,
        #                                 return_wiz.res_id,
        #                                 return_wiz.company_id.id,
        #                                 return_wiz.access_token
        #                             )
        # return request.redirect(link)

    @http.route(
        ["/submit_inquiry"], type="http", auth="public", website=True, csrf=False
    )
    def submit_inquiry(self, **post):
        if "csrf_token" in post:
            list(map(post.pop, ["csrf_token"]))
        if "date_of_arrival" in post and post.get("date_of_arrival"):
            start_dt = datetime.strptime(post.get("date_of_arrival"), "%Y-%m-%d").date()
            post.update({"date_of_arrival": start_dt})
        if "date_of_return" in post and post.get("date_of_return"):
            end_dt = datetime.strptime(post.get("date_of_return"), "%Y-%m-%d").date()
            post.update({"date_of_return": end_dt})
        lead = request.env["crm.lead"].sudo().create(post)
        template = request.env.ref("website_tour_agency.client_inquiry")
        template.sudo().send_mail(lead.id, force_send=True)
        return request.redirect("/contactus_thanks_travel")

