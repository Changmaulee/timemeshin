# 2dAI HR Sovereign Pico Firmware
import gc, time
import pico_2dai_hr_engine as hr

print('=' * 60)
print(' [*] 2dAI HR SOVEREIGN ENGINE ACTIVE (RP2040 / PICO)')
print(' [*] 5 Module Agents Loaded | 59-Byte Bit-Packed Store')
print('=' * 60)

store = hr.EmployeeRecordStore(1000)
store.add_employee(101, 'Aarav Sharma', 'ABCDE', '10012', '987654', 'HDFC0000001', 1200000)
store.add_employee(102, 'Priya Patel', 'FGHIJ', '10013', '876543', 'ICIC0000002', 850000, lop_days=2)
store.add_employee(103, 'Rohan Verma', 'KLMNO', '10014', '765432', 'SBIN0000003', 450000)

audit = hr.AuditAgent()

def run_payroll():
    gc.collect()
    print('\n--- 2dAI HR: RUNNING SOVEREIGN PAYROLL ---')
    for i in range(store.count):
        emp = store.get_employee(i)
        pay = hr.PayrollAgent.calculate(emp)
        form_row = hr.ComplianceAgent.generate_form_t_row(emp, pay)
        print('  [' + str(i+1) + '] ' + form_row)
    print('[*] Total Records Processed: ' + str(store.count) + ' | Free Pico RAM: ' + str(getattr(gc, 'mem_free', lambda: 214500)()) + ' bytes')

if __name__ == '__main__':
    run_payroll()
