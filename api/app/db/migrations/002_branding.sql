CREATE TABLE app_branding (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    logo TEXT
);

INSERT INTO menu (parent_id, name, path, permission_key, component, sort, is_system)
VALUES (
    (SELECT id FROM menu WHERE permission_key = 'system'),
    '品牌设置', '/system/branding', 'system:branding', 'view/system/branding.vue', 840, TRUE
);

INSERT INTO operation_permission (key, label, domain, operation)
VALUES ('branding.edit', '品牌设置·编辑', 'branding', 'edit');

INSERT INTO role_permission (role_id, permission_key)
SELECT id, 'branding.edit' FROM user_group WHERE is_admin;

INSERT INTO role_menu (role_id, menu_id)
SELECT g.id, m.id FROM user_group g CROSS JOIN menu m
WHERE g.is_admin AND m.permission_key = 'system:branding';

UPDATE mori_admin_schema_version SET version = 2;
