"""Render synthetic multi-document financial evidence in Vietnamese/English."""
from __future__ import annotations

Sectors={
    'manufacturing':('factory machinery and wholesale shipments','thiết bị nhà máy và hàng bán sỉ'),
    'retail':('store inventory and customer demand','hàng tồn kho cửa hàng và nhu cầu tiêu dùng'),
    'logistics':('fleet investment and transport contracts','đầu tư phương tiện và hợp đồng vận tải'),
    'software':('subscription delivery and technology assets','cung cấp thuê bao và tài sản công nghệ'),
}

def doc(doc_id,year,title,content,scope='consolidated',kind='financial_excerpt'):
    return dict(id=doc_id,document_id=f'fictional/{doc_id}',fiscal_year=year,title=title,
                statement_scope=scope,kind=kind,text=content)


def build_documents(w,language='en',layout=0):
    vi=language=='vi';docs={}
    unit='triệu USD' if vi else 'USD million'
    def f(n):
        return f'{n:,}' if not vi else f'{n:,}'.replace(',','.')
    def lines(pairs):
        if layout%3==0:return '\n'.join(f'{a}: {f(b)}' for a,b in pairs)
        if layout%3==1:return '\n'.join(f'• {a} — {f(b)}' for a,b in pairs)
        return ('| Chỉ tiêu | Giá trị |\n|---|---|\n' if vi else '| Metric | Value |\n|---|---|\n') + '\n'.join(f'| {a} | {f(b)} |' for a,b in pairs)
    for year in (2023,2024,2025):
        y=w['fiscal_years'][str(year)];s=str(year)[-2:]
        is_fields=[('Doanh thu thuần' if vi else 'Net revenue',y['revenue']),
                   ('Giá vốn' if vi else 'Cost of goods sold',y['cogs']),
                   ('Lợi nhuận gộp' if vi else 'Gross profit',y['gross_profit']),
                   ('Chi phí hoạt động tiền mặt' if vi else 'Cash operating expenses',y['cash_opex']),
                   ('Khấu hao' if vi else 'Depreciation',y['dep']),
                   ('Lợi nhuận hoạt động' if vi else 'Operating profit',y['operating_profit']),
                   ('Chi phí lãi vay' if vi else 'Interest expense',y['interest']),
                   ('Thuế TNDN hiện hành' if vi else 'Current income tax expense',y['tax']),
                   ('Lợi nhuận sau thuế' if vi else 'Net income',y['net_income'])]
        title=f'{year} Báo cáo kết quả kinh doanh hợp nhất' if vi else f'FY{year} Audited consolidated income statement'
        docs[f'IS{s}']=doc(f'IS{s}',year,title,f'{title}\n' + (f'Đơn vị: {unit}.\n' if vi else f'Unit: {unit}.\n') + lines(is_fields))
        bs_fields=[('Tiền và tương đương tiền' if vi else 'Cash and equivalents',y['cash']),
                   ('Phải thu khách hàng' if vi else 'Trade receivables',y['ar']),
                   ('Hàng tồn kho' if vi else 'Inventory',y['inventory']),
                   ('Tài sản ngắn hạn' if vi else 'Current assets',y['current_assets']),
                   ('Tài sản cố định thuần' if vi else 'Net PP&E',y['ppe']),
                   ('Tổng tài sản' if vi else 'Total assets',y['assets']),
                   ('Phải trả NCC' if vi else 'Trade payables',y['ap']),
                   ('Vay nợ ngắn hạn' if vi else 'Current debt',y['current_debt']),
                   ('Vay nợ dài hạn' if vi else 'Non-current debt',y['long_debt']),
                   ('Tổng nợ tài chính' if vi else 'Total borrowings',y['debt']),
                   ('Nợ ngắn hạn' if vi else 'Current liabilities',y['current_liabilities']),
                   ('Tổng nợ phải trả' if vi else 'Total liabilities',y['liabilities']),
                   ('Vốn chủ sở hữu' if vi else 'Total equity',y['equity'])]
        title=f'FY{year} Bảng cân đối kế toán hợp nhất' if vi else f'FY{year} Consolidated statement of financial position'
        docs[f'BS{s}']=doc(f'BS{s}',year,title,f'{title}\n'+(f'Đơn vị: {unit}.\n' if vi else f'Unit: {unit}.\n')+lines(bs_fields))
        cf_fields=[('CFO' if vi else 'Operating cash flow',y['cfo']),
                   ('CFI' if vi else 'Investing cash flow',y['cfi']),
                   ('CFF' if vi else 'Financing cash flow',y['cff']),
                   ('Tiền đầu kỳ' if vi else 'Opening cash',y['begin_cash']),
                   ('Tiền cuối kỳ' if vi else 'Closing cash',y['cash']),
                   ('Chi đầu tư TSCĐ' if vi else 'Cash CAPEX',y['capex']),
                   ('Khấu hao' if vi else 'Depreciation',y['dep']),
                   ('Biến động phải thu (tăng là dương)' if vi else 'Change in receivables (increase positive)',y['delta_ar']),
                   ('Biến động tồn kho (tăng là dương)' if vi else 'Change in inventory (increase positive)',y['delta_inventory']),
                   ('Biến động phải trả (tăng là dương)' if vi else 'Change in payables (increase positive)',y['delta_ap']),
                   ('Tiền vay mới' if vi else 'New borrowing proceeds',y['new_debt']),
                   ('Tiền trả gốc' if vi else 'Principal repayments',y['debt_repaid']),
                   ('Cổ tức tiền mặt' if vi else 'Cash dividends',y['dividends'])]
        title=f'FY{year} Lưu chuyển tiền tệ hợp nhất' if vi else f'FY{year} Consolidated cash flow statement'
        docs[f'CF{s}']=doc(f'CF{s}',year,title,f'{title}\n'+(f'Đơn vị: {unit}.\n' if vi else f'Unit: {unit}.\n')+lines(cf_fields))
    for year in (2024,2025):
        y=w['fiscal_years'][str(year)];ss=w['segments'][str(year)];s=str(year)[-2:]
        title=f'FY{year} Thuyết minh doanh thu theo mảng' if vi else f'FY{year} Segment note'
        fields=[('Mảng A - khách ngoài' if vi else 'Segment A external sales',ss['ext_a']),
                ('Mảng B - khách ngoài' if vi else 'Segment B external sales',ss['ext_b']),
                ('Giá vốn mảng A' if vi else 'Segment A COGS',ss['cogs_a']),
                ('Giá vốn mảng B' if vi else 'Segment B COGS',ss['cogs_b']),
                ('Doanh số nội bộ' if vi else 'Intragroup sales',ss['internal']),
                ('Tổng doanh số mảng trước loại trừ' if vi else 'Gross segment sales before eliminations',ss['gross_segment_sales'])]
        docs[f'SG{s}']=doc(f'SG{s}',year,title,f'{title}\n'+(f'Đơn vị: {unit}.\n' if vi else f'Unit: {unit}.\n')+lines(fields)+
            ('\nDoanh thu nội bộ phải loại khi tính doanh thu hợp nhất.' if vi else '\nIntragroup sales must be eliminated from consolidated group revenue.'))
    v25=w['fiscal_years']['2025'];v24=w['fiscal_years']['2024']
    doc_text=(f'Bản dự thảo chưa kiểm toán FY2025 ghi doanh thu {f(w["preliminary_revenue_25"])} {unit}; '
              f'bản hợp nhất đã kiểm toán FY2025 ghi {f(v25["revenue"])} {unit}. '
              f'Số so sánh FY2024 đã phân loại lại là {f(v24["revenue"])} {unit}, '
              f'bản FY2024 xuất bản ban đầu ghi {f(w["original_revenue_24"])} {unit}; '
              'điều chỉnh phân loại tương ứng ở thu nhập khác không thay đổi lợi nhuận ròng. '
              'Không có bảng chi tiết số tiền thu trực tiếp từ khách hàng hay lãi suất hợp đồng vay bình quân.'
              if vi else
              f'Unaudited FY2025 preliminary net revenue {f(w["preliminary_revenue_25"])} {unit}; '
              f'final audited FY2025 consolidated net revenue {f(v25["revenue"])} {unit}. '
              f'FY2024 restated comparable revenue {f(v24["revenue"])} {unit}, '
              f'whereas the originally-issued FY2024 sales figure was {f(w["original_revenue_24"])} {unit}; '
              'a presentation reclassification to other income kept net profit unchanged. '
              'No customer cash-receipts detail or borrowing-by-borrowing contractual coupon rates are disclosed.')
    docs['VN25']=doc('VN25',2025,'FY2025 Versions and policies' if not vi else 'Phiên bản và chính sách FY2025',doc_text,kind='version_note')
    stand_rev=round(v25['revenue']*0.72)
    stand_ca=round(v25['current_assets']*0.68)
    stand_cl=round(v25['current_liabilities']*0.64)
    standalone_text=(f'Báo cáo công ty mẹ riêng lẻ FY2025: doanh thu {f(stand_rev)} {unit}; tài sản ngắn hạn {f(stand_ca)}; nợ ngắn hạn {f(stand_cl)}. Đây KHÔNG PHẢI số hợp nhất.' if vi else
       f'FY2025 PARENT-ONLY, standalone, NOT consolidated: revenue {f(stand_rev)} {unit}; current assets {f(stand_ca)}; current liabilities {f(stand_cl)}.')
    docs['ST25']=doc('ST25',2025,'Parent standalone 2025' if not vi else 'Báo cáo riêng lẻ 2025',standalone_text,scope='standalone',kind='standalone_excerpt')
    sector_en,sector_vi=Sectors[w['sector']]
    if vi:
        docs['IN25']=doc('IN25',2025,'Điều kiện và phạm vi',
          f'Doanh nghiệp giả lập thuộc nhóm {w["sector"]}, tập trung vào {sector_vi}. '
          'Các dòng tiền hoạt động ghi nhận lãi vay và thuế chi tiền trong hoạt động kinh doanh. '
          'Khấu hao không phải chi tiền trong kỳ. Các biến động phải thu, tồn kho, phải trả nêu trong lưu chuyển tiền tệ đã loại biến động phi tiền mặt. '
          'Báo cáo hư cấu, không phải số liệu doanh nghiệp có thật. Chi tiết lãi suất khoản vay và thu tiền khách hàng không được công bố.',kind='policy_note')
    else:
        docs['IN25']=doc('IN25',2025,'Policies and scope',
          f'This fictional {w["sector"]} business is involved in {sector_en}. '
          'Interest and cash income taxes are included in operating cash flow. '
          'Depreciation is a noncash charge. Working capital changes exclude noncash reclassifications. '
          'All figures are fictional teaching examples and not real-company disclosures. '
          'Loan-by-loan coupon rates and actual customer cash collections are not disclosed.',kind='policy_note')
    return docs
