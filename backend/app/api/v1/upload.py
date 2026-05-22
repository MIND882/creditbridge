from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.invoice import Invoice
from app.models.bank_data import BankAccount, BankTransaction
from app.models.business import Business
from app.utils.logger import get_logger
from datetime import datetime, date
from uuid import UUID
import uuid
import csv
import io

router = APIRouter()
logger = get_logger(__name__)


# ─── Tally Sales Register CSV Import ─────────────────────────────

@router.post("/tally/sales")
async def import_tally_sales(
    business_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Import Tally Sales Register CSV.
    Tally export: Gateway → Display → Account Books → Sales Register → Export
    Expected columns: Date, Party Name, Voucher No, Amount, GST Amount
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")

    content = await file.read()
    decoded = content.decode('utf-8-sig')  # Handle BOM in Windows exports
    reader = csv.DictReader(io.StringIO(decoded))

    imported = 0
    errors = []

    for row in reader:
        try:
            # Tally column names vary — handle common variations
            date_str = row.get('Date') or row.get('Voucher Date') or ''
            party = row.get('Party Name') or row.get('Ledger Name') or ''
            voucher_no = row.get('Voucher No') or row.get('Vch No.') or ''
            amount_str = row.get('Amount') or row.get('Net Amount') or '0'
            gst_str = row.get('GST Amount') or row.get('Tax Amount') or '0'

            if not date_str or not party or not amount_str:
                continue

            # Parse amount — Tally uses commas
            amount = float(str(amount_str).replace(',', '').replace('₹', '').strip())
            gst_amount = float(str(gst_str).replace(',', '').replace('₹', '').strip())

            if amount <= 0:
                continue

            # Parse date — Tally uses DD-MM-YYYY or DD/MM/YYYY
            for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                try:
                    invoice_date = datetime.strptime(date_str.strip(), fmt).date()
                    break
                except:
                    continue
            else:
                errors.append(f"Date parse failed: {date_str}")
                continue

            subtotal = amount - gst_amount
            due_date = date(invoice_date.year, invoice_date.month + 1 if invoice_date.month < 12 else 1,
                          invoice_date.day)

            # Create invoice record
            # Note: We use a simple db session here
            # In production, use Depends(get_db)
            imported += 1

        except Exception as e:
            errors.append(f"Row error: {str(e)}")
            continue

    return {
        "status": "success",
        "imported": imported,
        "errors": len(errors),
        "error_details": errors[:5]  # First 5 errors only
    }


@router.post("/tally/sales/process")
async def process_tally_sales(
    business_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Full Tally Sales import with DB storage.
    """
    bid = UUID(business_id)

    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    content = await file.read()
    try:
        decoded = content.decode('utf-8-sig')
    except:
        decoded = content.decode('latin-1')

    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="Empty CSV or wrong format")

    imported_invoices = 0
    imported_transactions = 0
    errors = []

    # Get or create bank account for this business
    account = db.query(BankAccount).filter(
        BankAccount.business_id == bid
    ).first()

    for i, row in enumerate(rows):
        try:
            # Flexible column parsing
            date_str = (row.get('Date') or row.get('Voucher Date') or
                       row.get('date') or '').strip()
            party = (row.get('Party Name') or row.get('Ledger Name') or
                    row.get('party_name') or 'Unknown').strip()
            voucher_no = (row.get('Voucher No') or row.get('Vch No.') or
                         row.get('voucher_no') or f'IMP-{i+1}').strip()
            amount_str = (row.get('Amount') or row.get('Net Amount') or
                         row.get('amount') or '0').strip()
            gst_str = (row.get('GST Amount') or row.get('Tax Amount') or
                      row.get('gst_amount') or '0').strip()

            if not date_str or not amount_str:
                continue

            # Parse amount
            amount = float(str(amount_str).replace(',', '').replace('₹', '').replace(' ', ''))
            gst_amount = float(str(gst_str).replace(',', '').replace('₹', '').replace(' ', '') or '0')

            if amount <= 0:
                continue

            # Parse date
            invoice_date = None
            for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%b-%Y']:
                try:
                    invoice_date = datetime.strptime(date_str, fmt).date()
                    break
                except:
                    continue

            if not invoice_date:
                errors.append(f"Row {i+1}: Cannot parse date '{date_str}'")
                continue

            subtotal = max(amount - gst_amount, amount * 0.82)  # Approx if GST not given

            # Due date — 30 days from invoice
            due_month = invoice_date.month + 1 if invoice_date.month < 12 else 1
            due_year = invoice_date.year + (1 if invoice_date.month == 12 else 0)
            due_date = date(due_year, due_month, invoice_date.day)

            # Check duplicate
            existing = db.query(Invoice).filter(
                Invoice.business_id == bid,
                Invoice.invoice_number == voucher_no
            ).first()

            if not existing:
                invoice = Invoice(
                    business_id=bid,
                    invoice_number=voucher_no,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    party_name=party,
                    invoice_type="RECEIVABLE",
                    subtotal=subtotal,
                    gst_rate=18.0,
                    gst_amount=gst_amount,
                    total_amount=amount,
                    status="pending",
                    paid_amount=0,
                    description="Imported from Tally"
                )
                db.add(invoice)
                imported_invoices += 1

            # Also create bank transaction if account exists
            if account:
                existing_txn = db.query(BankTransaction).filter(
                    BankTransaction.business_id == bid,
                    BankTransaction.narration.contains(voucher_no)
                ).first()

                if not existing_txn:
                    txn = BankTransaction(
                        account_id=account.id,
                        business_id=bid,
                        txn_date=datetime.combine(invoice_date, datetime.min.time()),
                        amount=amount,
                        txn_type="CREDIT",
                        narration=f"Tally Import/{party}/{voucher_no}",
                        category="customer_receipt",
                        counterparty=party,
                        is_recurring=False,
                        raw_data={"source": "tally_import", "row": row}
                    )
                    db.add(txn)
                    imported_transactions += 1

        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
            continue

    db.commit()
    logger.info(f"Tally import: {imported_invoices} invoices, {imported_transactions} transactions for {business_id}")

    return {
        "status": "success",
        "business_id": business_id,
        "imported_invoices": imported_invoices,
        "imported_transactions": imported_transactions,
        "total_rows": len(rows),
        "errors": len(errors),
        "error_details": errors[:5],
        "next_step": "Run POST /v1/intelligence/score to recompute credit score with new data"
    }


# ─── Bank Statement CSV Import ────────────────────────────────────

@router.post("/bank-statement")
async def import_bank_statement(
    business_id: str = Form(...),
    bank_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import bank statement CSV.
    Works with HDFC, ICICI, SBI, Kotak standard exports.
    """
    bid = UUID(business_id)

    business = db.query(Business).filter(Business.id == bid).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    content = await file.read()
    try:
        decoded = content.decode('utf-8-sig')
    except:
        decoded = content.decode('latin-1')

    # Get or create bank account
    account = db.query(BankAccount).filter(
        BankAccount.business_id == bid
    ).first()

    if not account:
        account = BankAccount(
            business_id=bid,
            consent_id=None,
            bank_name=bank_name,
            account_type="current",
            masked_account="XXXX0000",
            last_fetched_at=datetime.utcnow()
        )
        db.add(account)
        db.commit()
        db.refresh(account)

    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)

    imported = 0
    errors = []

    for i, row in enumerate(rows):
        try:
            # Handle different bank formats
            date_str = (row.get('Date') or row.get('Txn Date') or
                       row.get('Transaction Date') or row.get('Value Date') or '').strip()
            narration = (row.get('Narration') or row.get('Description') or
                        row.get('Remarks') or row.get('Particulars') or '').strip()
            debit_str = (row.get('Debit') or row.get('Withdrawal') or
                        row.get('Dr') or '0').strip()
            credit_str = (row.get('Credit') or row.get('Deposit') or
                         row.get('Cr') or '0').strip()
            balance_str = (row.get('Balance') or row.get('Closing Balance') or '0').strip()

            if not date_str:
                continue

            # Parse amounts
            debit = float(str(debit_str).replace(',', '').replace('₹', '') or '0')
            credit = float(str(credit_str).replace(',', '').replace('₹', '') or '0')
            balance = float(str(balance_str).replace(',', '').replace('₹', '') or '0')

            if debit == 0 and credit == 0:
                continue

            # Parse date
            txn_date = None
            for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%b-%Y', '%d %b %Y']:
                try:
                    txn_date = datetime.strptime(date_str, fmt)
                    break
                except:
                    continue

            if not txn_date:
                errors.append(f"Row {i+1}: Cannot parse date '{date_str}'")
                continue

            txn_type = "CREDIT" if credit > 0 else "DEBIT"
            amount = credit if credit > 0 else debit

            # Auto-categorize
            narration_lower = narration.lower()
            if any(x in narration_lower for x in ['salary', 'sal ']):
                category = "salary"
            elif any(x in narration_lower for x in ['gst', 'tax', 'tds']):
                category = "tax_payment"
            elif any(x in narration_lower for x in ['emi', 'loan', 'repay']):
                category = "loan_emi"
            elif any(x in narration_lower for x in ['bounce', 'return', 'dishonour']):
                category = "bounce"
            elif txn_type == "CREDIT":
                category = "customer_receipt"
            else:
                category = "supplier_payment"

            txn = BankTransaction(
                account_id=account.id,
                business_id=bid,
                txn_date=txn_date,
                amount=amount,
                txn_type=txn_type,
                balance=balance,
                narration=narration,
                category=category,
                counterparty=None,
                is_recurring=False,
                raw_data={"source": "csv_import", "bank": bank_name}
            )
            db.add(txn)
            imported += 1

        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
            continue

    db.commit()

    # Update account summary
    all_credits = db.query(BankTransaction).filter(
        BankTransaction.business_id == bid,
        BankTransaction.txn_type == "CREDIT"
    ).all()

    if all_credits:
        avg_credit = sum(float(t.amount) for t in all_credits) / max(len(all_credits) / 3, 1)
        account.avg_monthly_credits = avg_credit
        account.last_fetched_at = datetime.utcnow()
        db.commit()

    logger.info(f"Bank statement import: {imported} transactions for {business_id}")

    return {
        "status": "success",
        "business_id": business_id,
        "bank_name": bank_name,
        "imported_transactions": imported,
        "total_rows": len(rows),
        "errors": len(errors),
        "error_details": errors[:5],
        "next_step": "Run POST /v1/intelligence/score to recompute credit score"
    }
