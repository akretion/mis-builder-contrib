# Copyright 2018 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, tools


class MisAccountAnalyticLine(models.Model):
    _name = "mis.account.analytic.line"
    _auto = False
    _description = "MIS Account Analytic Line"

    date = fields.Date()
    analytic_line_id = fields.Many2one(
        string="Analytic entry", comodel_name="account.analytic.line"
    )
    account_id = fields.Many2one(
        string="Account", comodel_name="account.account"
    )
    company_id = fields.Many2one(string="Company", comodel_name="res.company")
    balance = fields.Float(string="Balance")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    state = fields.Selection(
        [("draft", "Unposted"), ("posted", "Posted")], string="Status"
    )

    @api.multi
    def action_open_related_line(self):
        self.ensure_one()
        if self.line_type == 'move_line':
            return self.move_line_id.get_formview_action()
        else:
            return self.env['account.analytic.line'].browse(
                self.id).get_formview_action()

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, "mis_account_analytic_line")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW mis_account_analytic_line AS (
                SELECT
                    -- we use negative id to avoid duplicates and we don't use
                    -- ROW_NUMBER() because the performance was very poor
                    -aml.id as id,
                    CAST('move_line' AS varchar) as line_type,
                    Null AS analytic_line_id,
                    aml.date as date,
                    aml.account_id as account_id,
                    aml.company_id as company_id,
                    aml.analytic_account_id as analytic_account_id,
                    'posted'::VARCHAR as state,
                    aml.credit as credit,
                    aml.debit as debit,
                    aml.balance as balance
                FROM account_move_line as aml
                UNION ALL
                    SELECT
                    aal.id AS id,
                    CAST('analytic_line' AS varchar) as line_type,
                    aal.id AS analytic_line_id,
                    aal.date as date,
                    aal.general_account_id as account_id,
                    aal.company_id as company_id,
                    aal.account_id as analytic_account_id,
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
                WHERE employee_id IS NOT NULL
            )"""
        )
