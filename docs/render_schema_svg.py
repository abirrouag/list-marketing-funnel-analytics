"""
Renders Star Schema ERD to docs/schema.svg for visual documentation.
"""

import os

def generate_schema_svg(output_file="docs/schema.svg"):
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="100%" height="100%" style="background-color: #0f172a; font-family: system-ui, sans-serif;">
    <style>
        .table-box { fill: #1e293b; stroke: #3b82f6; stroke-width: 2; rx: 8; }
        .fact-box { fill: #1e1b4b; stroke: #818cf8; stroke-width: 2; rx: 8; }
        .title { fill: #f8fafc; font-size: 14px; font-weight: bold; }
        .field { fill: #94a3b8; font-size: 11px; }
        .pk { fill: #f59e0b; font-size: 11px; font-weight: bold; }
        .fk { fill: #38bdf8; font-size: 11px; }
        .link { stroke: #64748b; stroke-width: 1.5; stroke-dasharray: 4,4; }
        .header-text { fill: #f1f5f9; font-size: 20px; font-weight: bold; }
    </style>
    
    <text x="500" y="35" text-anchor="middle" class="header-text">Olist Marketing Funnel Star Schema Architecture</text>
    
    <!-- Dimensions Left -->
    <rect x="50" y="70" width="180" height="110" class="table-box"/>
    <text x="140" y="92" text-anchor="middle" class="title">dim_origin</text>
    <text x="65" y="115" class="pk">origin_key (PK)</text>
    <text x="65" y="135" class="field">origin_name</text>
    
    <rect x="50" y="210" width="180" height="130" class="table-box"/>
    <text x="140" y="232" text-anchor="middle" class="title">dim_seller</text>
    <text x="65" y="255" class="pk">seller_key (PK)</text>
    <text x="65" y="275" class="field">seller_id (UK)</text>
    <text x="65" y="295" class="field">lead_type, business_type</text>
    <text x="65" y="315" class="field">declared_monthly_revenue</text>

    <rect x="50" y="370" width="180" height="110" class="table-box"/>
    <text x="140" y="392" text-anchor="middle" class="title">dim_segment</text>
    <text x="65" y="415" class="pk">segment_key (PK)</text>
    <text x="65" y="435" class="field">segment_name</text>

    <!-- Facts Center -->
    <rect x="380" y="100" width="240" height="220" class="fact-box"/>
    <text x="500" y="125" text-anchor="middle" class="title" fill="#a5b4fc">fact_lead (Grain: MQL)</text>
    <text x="395" y="150" class="pk">lead_key (PK)</text>
    <text x="395" y="170" class="field">mql_id (UK)</text>
    <text x="395" y="190" class="fk">date_key_first_contact (FK)</text>
    <text x="395" y="210" class="fk">origin_key (FK)</text>
    <text x="395" y="230" class="fk">seller_key (FK)</text>
    <text x="395" y="250" class="fk">segment_key (FK)</text>
    <text x="395" y="270" class="field">is_won (0/1)</text>
    <text x="395" y="290" class="field">days_to_close</text>

    <rect x="380" y="350" width="240" height="200" class="fact-box"/>
    <text x="500" y="375" text-anchor="middle" class="title" fill="#a5b4fc">fact_order_item (Grain: Line Item)</text>
    <text x="395" y="400" class="pk">order_item_key (PK)</text>
    <text x="395" y="420" class="field">order_id, order_item_id</text>
    <text x="395" y="440" class="fk">date_key_purchase (FK)</text>
    <text x="395" y="460" class="fk">seller_key (FK)</text>
    <text x="395" y="480" class="fk">product_key (FK)</text>
    <text x="395" y="500" class="field">price, freight_value</text>
    <text x="395" y="520" class="field">days_after_won</text>

    <!-- Dimensions Right -->
    <rect x="770" y="70" width="180" height="110" class="table-box"/>
    <text x="860" y="92" text-anchor="middle" class="title">dim_date</text>
    <text x="785" y="115" class="pk">date_key (PK)</text>
    <text x="785" y="135" class="field">full_date, year, month</text>

    <rect x="770" y="210" width="180" height="110" class="table-box"/>
    <text x="860" y="232" text-anchor="middle" class="title">dim_product</text>
    <text x="785" y="255" class="pk">product_key (PK)</text>
    <text x="785" y="275" class="field">category_name_en</text>

    <rect x="770" y="370" width="180" height="110" class="table-box"/>
    <text x="860" y="392" text-anchor="middle" class="title">dim_customer</text>
    <text x="785" y="415" class="pk">customer_key (PK)</text>
    <text x="785" y="435" class="field">city, state</text>

    <!-- Connectors -->
    <line x1="230" y1="125" x2="380" y2="210" class="link"/>
    <line x1="230" y1="275" x2="380" y2="230" class="link"/>
    <line x1="230" y1="275" x2="380" y2="460" class="link"/>
    <line x1="620" y1="190" x2="770" y2="125" class="link"/>
    <line x1="620" y1="440" x2="770" y2="125" class="link"/>
    <line x1="620" y1="480" x2="770" y2="275" class="link"/>
    <line x1="620" y1="500" x2="770" y2="435" class="link"/>
</svg>"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Schema SVG rendered to {output_file}")

if __name__ == '__main__':
    generate_schema_svg()
