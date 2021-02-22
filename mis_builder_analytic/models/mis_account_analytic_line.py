# Copyright 2018 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, tools


class MisAccountAnalyticLineTagRel(models.Model):
    _name = 'account.analytic.tag.mis.account.analytic.line.rel'
    _auto = False
    _table = 'account_analytic_tag_mis_account_analytic_line_rel'

    account_analytic_tag_id = fields.Many2one(
        string="Analytic Tag",
        comodel_name="account.analytic.tag"
    )
    mis_account_analytic_line_id = fields.Many2one(
        string='MIS Analytic Line',
        comodel_name="mis.account.analytic.line"
    )


class MisAccountAnalyticLine(models.Model):
    _name = "mis.account.analytic.line"
    _auto = False
    _description = "MIS Account Analytic Line"

    date = fields.Date()
    analytic_line_id = fields.Many2one(
        string="Analytic entry", comodel_name="account.analytic.line"
    )
    account_id = fields.Many2one(
        string="Account", comodel_name="account.analytic.account"
    )
    company_id = fields.Many2one(string="Company", comodel_name="res.company")
    balance = fields.Float(string="Balance")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    state = fields.Selection(
        [("draft", "Unposted"), ("posted", "Posted")], string="Status"
    )

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, "mis_account_analytic_line")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW mis_account_analytic_line AS (
                SELECT
                    aal.id AS id,
                    aal.id AS analytic_line_id,
                    aal.date as date,
                    aal.account_id as account_id,
                    aal.company_id as company_id,
                    'posted'::VARCHAR as state,
                    CASE
                      WHEN aal.amount >= 0.0 THEN aal.amount
                      ELSE 0.0
                    END AS credit,
                    CASE
                      WHEN aal.amount < 0 THEN (aal.amount * -1)
                      ELSE 0.0
                    END AS debit,
                    aal.amount as balance
                FROM
                    account_analytic_line aal
            )"""
        )

        tools.drop_view_if_exists(self._cr, "account_analytic_tag_mis_account_analytic_line_rel")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW account_analytic_tag_mis_account_analytic_line_rel AS (
                SELECT
                    mis.id as mis_account_analytic_line_id,
                    tag_id as account_analytic_tag_id
                FROM mis_account_analytic_line as mis
                JOIN account_analytic_line_tag_rel as rel
                    ON mis.id=line_id
            )"""
        )
