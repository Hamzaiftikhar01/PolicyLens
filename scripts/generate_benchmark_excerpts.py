import fitz
import json
from pathlib import Path
import sys

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

# Verbatim legal excerpts for the 7 missing documents
EXCERPTS = {
    "constitution.pdf": {
        "title": "Constitution of the Islamic Republic of Pakistan",
        "sections": [
            {
                "header": "Article 7. Definition of the State",
                "text": "In this Part, unless the context otherwise requires, 'the State' means the Federal Government, Majlis-e-Shoora (Parliament), a Provincial Government, a Provincial Assembly, and such local or other authorities in Pakistan as are by law empowered to impose any tax or cess."
            },
            {
                "header": "Article 9. Security of person",
                "text": "No person shall be deprived of life or liberty save in accordance with law."
            },
            {
                "header": "Article 10A. Right to fair trial",
                "text": "For the determination of his civil rights and obligations or in any criminal charge against him a person shall be entitled to a fair trial and due process."
            },
            {
                "header": "Article 19. Freedom of speech, etc.",
                "text": "Every citizen shall have the right to freedom of speech and expression, and there shall be freedom of the press, subject to any reasonable restrictions imposed by law in the interest of the glory of Islam or the integrity, security or defence of Pakistan or any part thereof, friendly relations with foreign States, public order, decency or morality, or in relation to contempt of court, commission of or incitement to an offence."
            },
            {
                "header": "Article 19A. Right to information",
                "text": "Every citizen shall have the right to have access to information in all matters of public importance, subject to regulation and reasonable restrictions imposed by law."
            },
            {
                "header": "Article 25. Equality of citizens",
                "text": "All citizens are equal before law and are entitled to equal protection of law. There shall be no discrimination on the basis of sex alone. Nothing in this Article shall prevent the State from making any special provision for the protection of women and children."
            },
            {
                "header": "Article 34. Full participation of women in national life",
                "text": "Steps shall be taken to ensure full participation of women in all spheres of national life."
            },
            {
                "header": "Article 41. The President",
                "text": "There shall be a President of Pakistan who shall be the Head of State and shall represent the unity of the Republic. The President shall be elected by the members of an electoral college consisting of the members of both Houses and the Provincial Assemblies in accordance with the provisions of the Second Schedule."
            },
            {
                "header": "Article 63. Disqualifications for membership of Parliament",
                "text": "A person shall be disqualified from being elected or chosen as, and from being, a member of the Majlis-e-Shoora (Parliament), if: (a) he is of unsound mind and has been so declared by a competent court; or (b) he is an undischarged insolvent; or (c) he ceases to be a citizen of Pakistan, or acquires the citizenship of a foreign State; or (d) he holds an office of profit in the service of Pakistan..."
            },
            {
                "header": "Article 77. Tax to be levied by law",
                "text": "No tax shall be levied for the purposes of the Federation save by or under the authority of Act of Majlis-e-Shoora (Parliament)."
            },
            {
                "header": "Article 240. Appointments and conditions of service",
                "text": "Subject to the Constitution, the appointments to and the terms and conditions of service of persons in the service of Pakistan shall be determined- (a) in the case of the services of the Federation, posts in connection with the affairs of the Federation and All-Pakistan Services, by or under Act of Majlis-e-Shoora (Parliament)..."
            }
        ]
    },
    "pakistan_penal_code.pdf": {
        "title": "Pakistan Penal Code, 1860",
        "sections": [
            {
                "header": "Section 300. Qatl-i-amd",
                "text": "Whoever, with the intention of causing death or with the intention of causing bodily injury to a person, by doing an act which in the ordinary course of nature is likely to cause death, or with the knowledge that his act is so imminently dangerous that it must in all probability cause death, causes the death of such person, commits qatl-i-amd."
            },
            {
                "header": "Section 378. Theft",
                "text": "Whoever, intending to take dishonestly any moveable property out of the possession of any person without that person's consent, moves that property in order to such taking, is said to commit theft."
            },
            {
                "header": "Section 379. Punishment for theft",
                "text": "Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both."
            },
            {
                "header": "Section 499. Defamation",
                "text": "Whoever, by words either spoken or intended to be read, or by signs or by visible representations, makes or publishes any imputation concerning any person intending to harm, or knowing or having reason to believe that such imputation will harm, the reputation of such person, is said, except in the cases hereinafter excepted, to defame that person."
            },
            {
                "header": "Section 500. Punishment for defamation",
                "text": "Whoever defames another shall be punished with simple imprisonment for a term which may extend to two years, or with fine, or with both."
            }
        ]
    },
    "code_of_criminal_procedure.pdf": {
        "title": "Code of Criminal Procedure, 1898",
        "sections": [
            {
                "header": "Section 54. When police may arrest without warrant",
                "text": "Any police officer may, without an order from a Magistrate and without a warrant, arrest; First, any person who has been concerned in any cognizable offence or against whom a reasonable complaint has been made or credible information has been received... Fourth, any person in whose possession anything is found which may reasonably be suspected to be stolen property... Fifth, any person who has been proclaimed as an offender..."
            },
            {
                "header": "Section 154. Information in cognizable cases",
                "text": "Every information relating to the commission of a cognizable offence if given orally to an officer in charge of a police station, shall be reduced to writing by him or under his direction, and be read over to the informant; and every such information, whether given in writing or reduced to writing as aforesaid, shall be signed by the person giving it, and the substance thereof shall be entered in a book to be kept by such officer..."
            }
        ]
    },
    "code_of_civil_procedure.pdf": {
        "title": "Code of Civil Procedure, 1908",
        "sections": [
            {
                "header": "Section 11. Res Judicata",
                "text": "No Court shall try any suit or issue in which the matter directly and substantially in issue has been directly and substantially in issue in a former suit between the same parties, or between parties under whom they or any of them claim, litigating under the same title, in a Court competent to try such subsequent suit..."
            },
            {
                "header": "Order XXXIX, Rule 1. Cases in which temporary injunction may be granted",
                "text": "Where in any suit it is proved by affidavit or otherwise- (a) that any property in dispute in a suit is in danger of being wasted, damaged, or alienated by any party to the suit, or wrongfully sold in execution of a decree, the Court may by order grant a temporary injunction to restrain such act..."
            }
        ]
    },
    "elections_act_2017.pdf": {
        "title": "Elections Act, 2017",
        "sections": [
            {
                "header": "Section 9. Power of the Commission to declare a poll void",
                "text": "If, from facts apparent on the face of the record and after conducting summary inquiry, the Commission is satisfied that... the turnout of women voters is less than ten percent of the total votes polled in a constituency, the Commission may declare the poll void and order a new poll..."
            },
            {
                "header": "Section 206. Selection of candidates for general seats",
                "text": "A political party shall make selection of candidates for general seats, and shall ensure at least five percent representation of women candidates of the party in the general seats..."
            },
            {
                "header": "Section 232. Qualifications and disqualifications",
                "text": "The qualifications and disqualifications of a candidate or a member of Majlis-e-Shoora (Parliament) or a Provincial Assembly shall be such as are provided in Article 62 and Article 63 of the Constitution. Cases of disqualifications shall be processed and referred in accordance with the prescribed procedure."
            }
        ]
    },
    "right_of_access_to_information_act.pdf": {
        "title": "Right of Access to Information Act, 2017",
        "sections": [
            {
                "header": "Section 7. Exclusion of certain information",
                "text": "A public body shall not be required to disclose information which would, or is likely to, cause damage to the national security, defense, public order, international relations, or if it relates to third-party commercial interests, or if it constitutes private personal data, unless the public interest in disclosure outweighs the harm."
            },
            {
                "header": "Section 14. Time limit for responding",
                "text": "The designated officer shall, as soon as possible but in any case within ten working days of the receipt of the request, either provide the information or reject the request. Provided that this period may be extended by another ten working days if written reasons are supplied to the applicant."
            }
        ]
    },
    "civil_servants_act_1973.pdf": {
        "title": "Civil Servants Act, 1973",
        "sections": [
            {
                "header": "Section 5. Appointments",
                "text": "Appointments to the civil service of the Federation shall be made by the President, or by a person authorized by the President in that behalf, in the prescribed manner."
            },
            {
                "header": "Section 11. Termination of service",
                "text": "The service of a civil servant may be terminated without notice- (i) during the period of probation; (ii) on the abolition of post or reduction in cadre, in which case the services of the most junior person shall be terminated; or (iii) on the completion of the tenure of appointment."
            }
        ]
    }
}

def generate_pdfs():
    print("==================================================")
    print(" Generating Verbatim Pakistani Legal PDF Excerpts")
    print("==================================================")
    
    config.BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    
    for filename, doc_data in EXCERPTS.items():
        dest_path = config.BENCHMARK_DIR / filename
        print(f"[*] Creating: {filename} ({doc_data['title']})")
        
        doc = fitz.open()
        page = doc.new_page()
        
        # Draw header
        page.insert_text(
            (50, 40), 
            doc_data["title"].upper(), 
            fontsize=12, 
            fontname="hebo", 
            color=(0.1, 0.1, 0.15)
        )
        
        # Separator line
        shape = page.new_shape()
        shape.draw_line((50, 52), (540, 52))
        shape.finish(color=(0.3, 0.3, 0.35), width=1)
        shape.commit()
        
        # Write provisions
        y_offset = 70
        for sec in doc_data["sections"]:
            # If approaching bottom, add new page
            if y_offset > 650:
                page = doc.new_page()
                y_offset = 60
                
            # Render section header
            page.insert_text(
                (50, y_offset), 
                sec["header"], 
                fontsize=10, 
                fontname="hebo", 
                color=(0.15, 0.15, 0.25)
            )
            y_offset += 15
            
            # Render section text wrapped inside textbox
            rect = fitz.Rect(50, y_offset, 540, y_offset + 120)
            # insert_textbox returns remaining height or lines, wraps cleanly
            text_height = page.insert_textbox(
                rect, 
                sec["text"], 
                fontsize=9.5, 
                fontname="helv", 
                color=(0.2, 0.2, 0.2), 
                align=0
            )
            
            # Estimate height based on length
            lines = len(sec["text"]) // 65 + 1
            y_offset += (lines * 14) + 20
            
        doc.save(str(dest_path))
        doc.close()
        print(f"  [SUCCESS] Saved as {filename} ({dest_path.stat().st_size / 1024:.2f} KB)")
        
    print("\n[OK] All 7 Pakistani legal PDFs generated successfully!")

if __name__ == "__main__":
    generate_pdfs()
