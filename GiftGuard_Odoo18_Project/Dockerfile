FROM odoo:18.0

USER root

COPY --chown=odoo:odoo addons/custom/ /mnt/extra-addons/custom/
COPY --chown=odoo:odoo config/odoo.conf /etc/odoo/odoo.conf

USER odoo
