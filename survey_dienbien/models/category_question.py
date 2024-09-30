from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

class CategoryQuestion(models.Model):
    _name = 'category.question'
    _description = "Category Question"
    _parent_name = 'parent_id'
    _parent_order = 'name'
    _rec_name = 'name'

    name = fields.Char('Tên nhóm', required=True)
    code = fields.Char('Mã nhóm')
    parent_id = fields.Many2one('category.question', string='Danh mục cha', ondelete='cascade')
    child_ids = fields.One2many('category.question', 'parent_id', string='Danh mục con')
    note = fields.Char('Ghi chú')
    path = fields.Char(string='Đường dẫn quan hệ', compute='_compute_path', store=True)

    @api.depends('name', 'parent_id')
    def _compute_path(self):
        for record in self:
            record.path = record._get_full_path()

    def _get_full_path(self):
        self.ensure_one()
        if self.parent_id:
            return f"{self.parent_id._get_full_path()} --> {self.name}"
        else:
            return self.name

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        for category in self:
            parent = category.parent_id
            while parent:
                if parent == category:
                    raise ValidationError("Danh mục không thể được đặt làm danh mục cha của chính nó.")
                parent = parent.parent_id

    def _check_recursive_loop(self):
        for category in self:
            visited_categories = set()
            current = category
            while current:
                if current.id in visited_categories:
                    raise ValidationError("Danh mục không thể tạo vòng lặp (ví dụ: A -> B -> C -> A).")
                visited_categories.add(current.id)
                current = current.parent_id

    @api.model_create_multi
    def create(self, vals_list):
        # Gọi phương thức create của lớp cha để xử lý batch create
        records = super(CategoryQuestion, self).create(vals_list)

        # Gọi hàm _check_recursive_loop cho từng bản ghi
        for record in records:
            record._check_recursive_loop()

        return records

    def write(self, vals):
        # Ghi đè phương thức write để xử lý cho tất cả các bản ghi
        result = super(CategoryQuestion, self).write(vals)

        # Gọi hàm _check_recursive_loop cho từng bản ghi
        for record in self:
            record._check_recursive_loop()

        return result