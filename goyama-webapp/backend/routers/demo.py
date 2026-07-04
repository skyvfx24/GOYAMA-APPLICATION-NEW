import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
import pandas as pd
import yaml
from loguru import logger

from backend.config.settings import settings
from backend.services.file_manager import file_manager
from backend.models.response_models import UploadResponse

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

def ensure_demo_data_exists():
    """Generates synthetic spreadsheets and configs in the demo_data directory."""
    demo_dir = settings.DEMO_DATA_DIR
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate default_config.yaml
    config_path = settings.DEFAULT_CONFIG_PATH
    default_config = {
        "engine": {
            "run_mode": "TOLERANT",
            "amount_epsilon": 0.05,
            "date_days_tolerance": 3
        },
        "matching": {
            "primary_key": "pan",
            "enable_fuzzy_matching": True,
            "fuzzy_threshold": 0.90,
            "fuzzy_secondary_keys": ["mobile", "email"],
            "source_overrides": {
                "CAMS": {
                    "enable_fuzzy_matching": True,
                    "fuzzy_threshold": 0.88
                }
            }
        },
        "validation": {
            "require_pan": True,
            "validate_kyc_status": True,
            "validate_fatca_status": True,
            "allowed_kyc_statuses": ["VERIFIED", "EXEMPT"],
            "allowed_fatca_statuses": ["COMPLIANT"],
            "suppress_missing_in_report_for_incomplete_crm": True
        },
        "reporting": {
            "default_output_formats": ["excel", "csv", "json"],
            "redact_sensitive_fields": False,
            "severity_mappings": {
                "MISSING_IN_CRM": "CRITICAL",
                "MISSING_IN_REPORT": "HIGH",
                "AMOUNT_MISMATCH": "CRITICAL",
                "NAME_MISMATCH": "HIGH",
                "MOBILE_MISMATCH": "MEDIUM",
                "EMAIL_MISMATCH": "MEDIUM",
                "KYC_MISMATCH": "MEDIUM",
                "FATCA_MISMATCH": "HIGH",
                "DATE_MISMATCH": "LOW",
                "FIELD_MISSING": "MEDIUM",
                "FIELD_EMPTY": "MEDIUM",
                "INCOMPLETE_CRM_RECORD": "MEDIUM"
            }
        },
        "sources": {
            "CAMS": {
                "available_fields": ["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "total_amount", "folio_number", "tax_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "required_fields": ["pan", "investor_name"],
                "compare": ["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "total_amount", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "validations": ["pan_format", "mobile_format", "email_format"]
            },
            "KFINTECH": {
                "available_fields": ["pan", "investor_name", "mobile", "total_amount", "folio_number", "investor_status", "kyc_status", "fatca_status", "tax_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "required_fields": ["pan", "investor_name"],
                "compare": ["pan", "investor_name", "mobile", "total_amount", "investor_status", "kyc_status", "fatca_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "validations": ["pan_format", "mobile_format"]
            },
            "BSE": {
                "available_fields": ["pan", "investor_name", "email", "total_amount", "investor_status", "kyc_status", "fatca_status", "tax_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "required_fields": ["pan", "investor_name"],
                "compare": ["pan", "investor_name", "email", "total_amount", "investor_status", "kyc_status", "fatca_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "validations": ["pan_format", "email_format"]
            },
            "NSE": {
                "available_fields": ["pan", "investor_name", "mobile", "email", "total_amount", "investor_status", "kyc_status", "fatca_status", "tax_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "required_fields": ["pan", "investor_name"],
                "compare": ["pan", "investor_name", "mobile", "email", "total_amount", "investor_status", "kyc_status", "fatca_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "validations": ["pan_format", "mobile_format", "email_format"]
            },
            "PDF_CAS": {
                "available_fields": ["pan", "investor_name", "mobile", "email", "total_amount", "folio_number", "tax_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "required_fields": ["pan", "investor_name"],
                "compare": ["pan", "investor_name", "mobile", "total_amount", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "validations": ["pan_format", "mobile_format"]
            },
            "INSURANCE": {
                "available_fields": ["pan", "investor_name", "mobile", "email", "total_amount", "folio_number", "tax_status", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "required_fields": ["pan", "investor_name"],
                "compare": ["pan", "investor_name", "mobile", "email", "total_amount", "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address", "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn"],
                "validations": ["pan_format", "mobile_format", "email_format"]
            }
        }
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False)
    logger.info("Demo config generated.")

    # 2. Generate sample_crm.xlsx
    crm_path = demo_dir / "sample_crm.xlsx"
    crm_data = {
        "PAN": [
            "ABCDE1234F",  # Clean Match
            "XYZWP5678Q",  # Mobile/Email Mismatch
            "MNOPE9999A",  # CRM Only (Missing in report)
            "DEFGH4444X",  # Name Mismatch (Rohit Gupta)
            "JKLMN3333Z",  # Amount Mismatch (Anita Sen)
            "SCENARIO18P", # Scenario 18: Status Mismatch
            "SCENARIO19P", # Scenario 19: Status Field Missing in report
            "SCENARIO20P", # Scenario 20: Status Field Empty in report
            "SCENARIOMIN", # Minor Account
            "CMSPJ2820B"   # Incomplete CRM Record (Suppress Missing in Report -> INCOMPLETE_CRM_RECORD)
        ],
        "Investor Name": [
            "RAMESH SHARMA",
            "SITA VERMA",
            "AMIT KHAN",
            "ROHIT GUPTA",
            "ANITA SEN",
            "SCENARIO 18 INVESTOR",
            "SCENARIO 19 INVESTOR",
            "SCENARIO 20 INVESTOR",
            "SCENARIO MINOR INVESTOR",
            "INCOMPLETE CRM INVESTOR"
        ],
        "Mobile": [
            "9876543210",
            "9999999999",  # Will mismatch in report
            "9888888888",
            "9777777777",
            "9666666666",
            "9555555555",
            "9444444444",
            "9333333333",
            "9222222222",
            None  # Incomplete
        ],
        "Email": [
            "ramesh@gmail.com",
            "sita@gmail.com",  # Will mismatch in report
            "amit@gmail.com",
            "rohit@gmail.com",
            "anita@gmail.com",
            "scenario18@gmail.com",
            "scenario19@gmail.com",
            "scenario20@gmail.com",
            "minor@gmail.com",
            None  # Incomplete
        ],
        "KYC Status": ["VERIFIED", "VERIFIED", "VERIFIED", "EXEMPT", "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED", "UNKNOWN"],
        "FATCA Status": ["COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "UNKNOWN"],
        "Investor Status": ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "UNKNOWN"],
        "Tax Status": ["INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "ON BEHALF OF MINOR", "INDIVIDUAL"],
        "Total Amount": [75000.50, 120000.00, 45000.00, 25000.00, 50000.00, 10000.00, 20000.00, 30000.00, 40000.00, 0.00],
        "Client ID": ["CRM_01", "CRM_02", "CRM_03", "CRM_04", "CRM_05", "CRM_18", "CRM_19", "CRM_20", "CRM_MIN", "CMSPJ2820B"],
        "Date of Birth": ["12 Apr 1985", "15 May 1990", "20 Jun 1988", "10 Jul 1992", "25 Aug 1980", "12 Apr 1985", "12 Apr 1985", "12 Apr 1985", "12 Apr 1985", None],
        "Bank Name": ["HDFC Bank", "ICICI Bank", "SBI", "AXIS Bank", "HDFC Bank", "HDFC Bank", "HDFC Bank", "HDFC Bank", "HDFC Bank", None],
        "Bank Account": ["601050254647", "123456789012", "987654321098", "555555555555", "601050254647", "601050254647", "601050254647", "601050254647", "601050254647", None],
        "IFSC": ["HDFC0000060", "ICIC0001234", "SBIN0009876", "UTIB0000555", "HDFC0000060", "HDFC0000060", "HDFC0000060", "HDFC0000060", "HDFC0000060", None],
        "Registered Address": ["Tulsi Aura, Sector 8, Ghansoli, 400701", "Address 2", "Address 3", "Address 4", "Address 5", "Address 6", "Address 7", "Address 8", "Address 9", None],
        "Mode of Holding": ["Individual", "Joint", "Single", "Individual", "Individual", "Individual", "Individual", "Individual", "Individual", None],
        "Nominee 1": ["Pooja Dhiraj Modi", "Nominee B", "Nominee C", "Nominee D", "Nominee E", "Nominee F", "Nominee G", "Nominee H", "Nominee I", None],
        "Nominee relation / %": ["Spouse / 100%", "Mother / 50%", "Son / 100%", "Father / 100%", "Spouse / 100%", "Spouse / 100%", "Spouse / 100%", "Spouse / 100%", "Spouse / 100%", None],
        "Distributor (ARN)": ["Dhiraj Modi (lead src)", "ARN-12345", "ARN-98765", "ARN-11111", "ARN-22222", "ARN-33333", "ARN-44444", "ARN-55555", "ARN-66666", None]
    }
    pd.DataFrame(crm_data).to_excel(crm_path, index=False)
    logger.info("Demo CRM file generated.")

    # 3. Generate sample_cams.xlsx (CAMS report)
    cams_path = demo_dir / "sample_cams.xlsx"
    cams_data = {
        "PAN": [
            "ABCDE1234F",  # Ramesh Sharma (Clean Match)
            "JKLMN3333Z",  # Anita Sen (Amount mismatch: 48000.00 vs 50000.00)
            "SCENARIO18P", # Scenario 18: Status Mismatch (INACTIVE)
            "SCENARIO20P", # Scenario 20: Status Field Empty
            "SCENARIOMIN"  # Minor Account
        ],
        "Investor Name": [
            "RAMESH SHARMA",
            "ANITA SEN",
            "SCENARIO 18 INVESTOR",
            "SCENARIO 20 INVESTOR",
            "SCENARIO MINOR INVESTOR"
        ],
        "Folio Number": ["9876543/21", "1122334/45", "1818181/18", "2020202/20", "9999999/99"],
        "Total Amount": [75000.50, 48000.00, 10000.00, 30000.00, 40000.00],
        "KYC Status": ["VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED"],
        "FATCA Status": ["COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT"],
        "Investor Status": ["ACTIVE", "ACTIVE", "INACTIVE", "", "ACTIVE"],
        "Tax Status": ["INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "MINOR"],
        "Mobile": ["9876543210", "9666666666", "9555555555", "9333333333", "9222222222"],
        "Email": ["ramesh@gmail.com", "anita@gmail.com", "scenario18@gmail.com", "scenario20@gmail.com", "minor@gmail.com"],
        "Date of Birth": ["12 Apr 1985", "25 Aug 1980", "12 Apr 1985", "12 Apr 1985", "12 Apr 1985"],
        "Bank Name": ["HDFC BANK", "HDFC BANK", "HDFC BANK", "HDFC BANK", "HDFC BANK"],
        "Bank Account": ["601050254647", "601050254647", "601050254647", "601050254647", "601050254647"],
        "IFSC": ["HDFC0000060", "HDFC0000060", "HDFC0000060", "HDFC0000060", "HDFC0000060"],
        "Registered Address": ["Tulsi Aura, Sector 8, Ghansoli, 400701", "Address 5", "Address 6", "Address 8", "Address 9"],
        "Mode of Holding": ["SINGLE / Individual", "Individual", "Individual", "Individual", "Individual"],
        "Nominee 1": ["POOJA DHIRAJ MODI", "Nominee E", "Nominee F", "Nominee H", "Nominee I"],
        "Nominee relation / %": ["Spouse / 100%", "Spouse / 100%", "Spouse / 100%", "Spouse / 100%", "Spouse / 100%"],
        "Distributor (ARN)": ["ARN 95748 GOYAMA", "ARN-22222", "ARN-33333", "ARN-55555", "ARN-66666"]
    }
    pd.DataFrame(cams_data).to_excel(cams_path, index=False)
    logger.info("Demo CAMS file generated.")

    # 4. Generate sample_kfintech.xlsx (KFintech report)
    kfin_path = demo_dir / "sample_kfintech.xlsx"
    kfin_data = {
        "PAN_NO": [
            "XYZWP5678Q"   # Sita Verma (mismatch contacts)
        ],
        "Client Name": [
            "SITA VERMA"
        ],
        "Folio": ["7766554/90"],
        "Amount": [120000.00],
        "Mobile": ["8888888888"],  # CRM has 9999999999
        "Status": ["ACTIVE"],
        "KYC": ["VERIFIED"],
        "FATCA": ["COMPLIANT"],
        "Tax Status": ["INDIVIDUAL"],
        "Date of Birth": ["15 May 1990"],
        "Bank Name": ["ICICI Bank"],
        "Bank Account": ["123456789012"],
        "IFSC": ["ICIC0001234"],
        "Registered Address": ["Address 2"],
        "Mode of Holding": ["Joint"],
        "Nominee 1": ["Nominee B"],
        "Nominee relation / %": ["Mother / 50%"],
        "Distributor (ARN)": ["ARN-12345"]
    }
    pd.DataFrame(kfin_data).to_excel(kfin_path, index=False)
    logger.info("Demo KFintech file generated.")

    # 5. Generate sample_bse.xlsx (BSE report)
    bse_path = demo_dir / "sample_bse.xlsx"
    bse_data = {
        "BSE_PAN": [
            "ABCDE1234F",  # Ramesh
            "TUVWX1111Y",  # Report Only (Missing in CRM)
            "SCENARIO19P"  # Scenario 19: Status Field Missing in report
        ],
        "BSE Client Name": [
            "RAMESH SHARMA",
            "VIJAY PATEL",
            "SCENARIO 19 INVESTOR"
        ],
        "Email": [
            "ramesh@gmail.com",
            "vijay@gmail.com",
            "scenario19@gmail.com"
        ],
        "Amount": [50000.00, 80000.00, 20000.00],  # Note: Ramesh amount is lower here, but overall total check is standard
        "Tax Status": ["INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL"]
    }
    pd.DataFrame(bse_data).to_excel(bse_path, index=False)
    logger.info("Demo BSE file generated.")

    # 6. Generate sample_nse.xlsx (NSE report)
    nse_path = demo_dir / "sample_nse.xlsx"
    nse_data = {
        "nse_pan": [
            "DEFGH4444X"   # Rohit Gupta (Fuzzy Name match "Rohit Kumar Gupta")
        ],
        "nse_client_name": [
            "ROHIT KUMAR GUPTA"
        ],
        "Mobile": ["9777777777"],
        "Email": ["rohit@gmail.com"],
        "Balance": [25000.00],
        "Status": ["ACTIVE"],
        "KYC": ["VERIFIED"],
        "FATCA": ["COMPLIANT"],
        "Tax Status": ["INDIVIDUAL"]
    }
    pd.DataFrame(nse_data).to_excel(nse_path, index=False)
    logger.info("Demo NSE file generated.")

    # 7. Copy sample PDF statement
    pdf_dest = demo_dir / "sample_cas.pdf"
    pdf_src = settings.PROJECT_ROOT / "sample_run" / "input" / "Aakash Jamnik BAjaj.pdf"
    if pdf_src.exists():
        try:
            shutil.copy2(pdf_src, pdf_dest)
            logger.info("Demo PDF statement copied from sample input.")
        except Exception as e:
            logger.error(f"Failed to copy PDF statement: {e}")
    else:
        logger.warning(f"Source PDF not found at {pdf_src}")

    # 8. Generate sample_insurance.xlsx
    ins_path = demo_dir / "sample_insurance.xlsx"
    ins_data = {
        "PAN": [
            "ABCDE1234F",  # Ramesh (matches)
            "XYZWP5678Q"   # Sita Verma
        ],
        "Policyholder": [
            "RAMESH SHARMA",
            "SITA VERMA"
        ],
        "Policy No": ["INS/999888", "INS/777666"],
        "Premium": [5000.00, 15000.00],
        "Mobile": ["9876543210", "8888888888"],
        "Email": ["ramesh@gmail.com", "sita@gmail.com"],
        "Bank Name": ["HDFC BANK", "ICICI BANK"],
        "Account Number": ["601050254647", "123456789012"],
        "IFSC": ["HDFC0000060", "ICIC0001234"]
    }
    pd.DataFrame(ins_data).to_excel(ins_path, index=False)
    logger.info("Demo Insurance file generated.")


@router.post("/load")
async def load_demo_data():
    """Loads all pre-packaged demo files into the active temp session directory."""
    # Ensure all demo files exist on disk
    try:
        ensure_demo_data_exists()
    except Exception as e:
        logger.error(f"Failed to verify/generate demo data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize demo data files: {e}")
        
    demo_dir = settings.DEMO_DATA_DIR
    
    # Files to copy
    file_mappings = {
        "crm": ("sample_crm.xlsx", "CRM"),
        "cams": ("sample_cams.xlsx", "CAMS"),
        "kfintech": ("sample_kfintech.xlsx", "KFINTECH"),
        "bse": ("sample_bse.xlsx", "BSE"),
        "nse": ("sample_nse.xlsx", "NSE"),
        "pdf_cas": ("sample_cas.pdf", "PDF_CAS"),
        "insurance": ("sample_insurance.xlsx", "INSURANCE"),
        "config": ("default_config.yaml", "CONFIG")
    }
    
    results = {}
    for key, (filename, source_type) in file_mappings.items():
        src_path = demo_dir / filename
        if not src_path.exists():
            continue
            
        file_id = str(uuid.uuid4())
        
        # Read and save in FileManager
        with open(src_path, "rb") as f:
            content = f.read()
            
        file_manager.save_file(file_id, filename, content)
        
        # Structure as upload response
        upload_resp = UploadResponse(
            file_id=file_id,
            filename=filename,
            source_type=source_type
        )
        
        if key == "crm":
            results["crm"] = upload_resp
        elif key == "config":
            results["config"] = upload_resp
        else:
            if "reports" not in results:
                results["reports"] = []
            results["reports"].append(upload_resp)
            
    return results
