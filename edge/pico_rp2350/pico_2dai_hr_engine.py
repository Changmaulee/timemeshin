# 2dAI HR Sovereign Engine for Raspberry Pi Pico (RP2040 / RP2350)
import gc, struct, time

EMP_STRUCT_FMT = '>H14s5s5s6sHIHB8s2s2sHI'
EMP_RECORD_SIZE = struct.calcsize(EMP_STRUCT_FMT)
BANK_DICT = ['HDFC0000001', 'ICIC0000002', 'SBIN0000003', 'UTIB0000004', 'KKBK0000005', 'PUNB0000006']

def pad_str(s, length):
    s = str(s)[:length]
    return (s + ' ' * (length - len(s))).encode('ascii')

class EmployeeRecordStore:
    def __init__(self, max_employees=1000):
        self.max_employees = max_employees
        self.count = 0
        self.buffer = bytearray(max_employees * EMP_RECORD_SIZE)

    def add_employee(self, emp_id, name, pan, uan, bank_acc, ifsc, ctc, basic_pct=50, hra_pct=20, 
                     is_new_regime=1, pf_opt=1, esic_opt=1, pt_state=1, leaves=(2, 1, 1, 0), lop_days=0):
        if self.count >= self.max_employees:
            raise OverflowError('Capacity reached!')
        name_bytes = pad_str(name, 14)
        pan_bytes = pad_str(pan, 5)
        uan_bytes = pad_str(uan, 5)
        bank_bytes = pad_str(bank_acc, 6)
        ifsc_idx = BANK_DICT.index(ifsc) if ifsc in BANK_DICT else 0
        split_ratios = ((basic_pct & 0x1F) << 5) | (hra_pct & 0x1F)
        flags = (is_new_regime & 1) | ((pf_opt & 1) << 1) | ((esic_opt & 1) << 2) | ((pt_state & 3) << 3)
        attend_bytes = b'\x55\x55\x55\x55\x55\x55\x55\x55'
        cl, sl, el, comp = leaves
        leaf_bytes = bytes([((cl & 0xF) << 4) | (sl & 0xF), ((el & 0xF) << 4) | (comp & 0xF)])
        lop_ot = bytes([lop_days & 0xFF, 0])
        tds_override = 0
        causal_hash = 0xA1B2C3D4

        raw = struct.pack(
            EMP_STRUCT_FMT, emp_id, name_bytes, pan_bytes, uan_bytes, bank_bytes,
            ifsc_idx, int(ctc), split_ratios, flags, attend_bytes, leaf_bytes, lop_ot, tds_override, causal_hash
        )
        offset = self.count * EMP_RECORD_SIZE
        self.buffer[offset:offset+EMP_RECORD_SIZE] = raw
        self.count += 1
        return self.count - 1

    def get_employee(self, index):
        if index < 0 or index >= self.count:
            return None
        offset = index * EMP_RECORD_SIZE
        raw = self.buffer[offset:offset+EMP_RECORD_SIZE]
        un = struct.unpack(EMP_STRUCT_FMT, raw)
        return {
            'emp_id': un[0],
            'name': un[1].decode('ascii').strip(),
            'pan': un[2].decode('ascii').strip(),
            'uan': un[3].decode('ascii').strip(),
            'bank_acc': un[4].decode('ascii').strip(),
            'ifsc': BANK_DICT[un[5]],
            'ctc': un[6],
            'basic_pct': (un[7] >> 5) & 0x1F,
            'hra_pct': un[7] & 0x1F,
            'pf_opt': bool((un[8] >> 1) & 1),
            'esic_opt': bool((un[8] >> 2) & 1),
            'lop_days': un[11][0],
            'causal_hash': hex(un[13])
        }

class PayrollAgent:
    @staticmethod
    def calculate(emp, month_days=30):
        gross_monthly = emp['ctc'] / 12.0
        worked_days = max(0, month_days - emp['lop_days'])
        pro_rata = worked_days / month_days
        basic = (gross_monthly * (emp['basic_pct'] / 100.0)) * pro_rata
        hra = (gross_monthly * (emp['hra_pct'] / 100.0)) * pro_rata
        special = (gross_monthly - (gross_monthly * ((emp['basic_pct'] + emp['hra_pct']) / 100.0))) * pro_rata
        earned_gross = basic + hra + special
        epf = min(basic, 15000) * 0.12 if emp['pf_opt'] else 0
        esic = earned_gross * 0.0075 if (emp['esic_opt'] and earned_gross <= 21000) else 0
        pt = 200 if earned_gross > 15000 else 0
        taxable_annual = max(0, (earned_gross * 12) - 75000)
        tds_annual = 0
        if taxable_annual > 1500000: tds_annual = 150000 + (taxable_annual - 1500000) * 0.30
        elif taxable_annual > 1200000: tds_annual = 90000 + (taxable_annual - 1200000) * 0.20
        elif taxable_annual > 700000: tds_annual = (taxable_annual - 700000) * 0.10
        tds_monthly = tds_annual / 12.0
        net = earned_gross - (epf + esic + pt + tds_monthly)
        return {'basic': round(basic, 2), 'hra': round(hra, 2), 'gross': round(earned_gross, 2),
                'epf': round(epf, 2), 'esic': round(esic, 2), 'pt': pt, 'tds': round(tds_monthly, 2), 'net': round(net, 2)}

class ComplianceAgent:
    @staticmethod
    def generate_form_t_row(emp, pay):
        name_padded = emp['name'] + ' ' * (14 - len(emp['name']))
        return 'EMP' + str(emp['emp_id']) + ' | ' + name_padded + ' | Gross:Rs ' + str(pay['gross']) + ' | EPF:Rs ' + str(pay['epf']) + ' | Net:Rs ' + str(pay['net'])

class AuditAgent:
    def __init__(self):
        self.is_frozen = False
    def freeze(self):
        self.is_frozen = True
        return 'Payroll State FROZEN'
    def unfreeze(self):
        self.is_frozen = False
        return 'Payroll State UNFROZEN'
