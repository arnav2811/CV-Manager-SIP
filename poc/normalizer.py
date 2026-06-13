import csv
import re
import os
import time
from rapidfuzz import process, fuzz

class Normalizer:
    def __init__(self, data_dir='../data'):
        self.data_dir = data_dir
        self.degree_aliases = {}  # normalized -> canonical
        self.field_aliases = {}   # normalized -> canonical
        self.canonical_degrees = set()
        
        self.load_aliases()
        
    def load_aliases(self):
        degree_csv = os.path.join(self.data_dir, 'degree_aliases.csv')
        field_csv = os.path.join(self.data_dir, 'field_of_study_aliases.csv')
        
        if not os.path.exists(degree_csv) or not os.path.exists(field_csv):
            print("Error: Alias CSVs not found. Run generate_data.py first.")
            return

        with open(degree_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.degree_aliases[row['normalized']] = row['canonical_name']
                self.canonical_degrees.add(row['canonical_name'])
                
        with open(field_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic normalization for field alias lookup
                norm_field = row['alias'].strip().lower().replace('.', '')
                self.field_aliases[norm_field] = row['canonical_field']

        print(f"Loading alias dictionary... {len(self.degree_aliases)} entries loaded.")
        print(f"Loading field dictionary... {len(self.field_aliases)} entries loaded.")

    def clean(self, raw_string):
        """ Lowercases, removes dots, strips spaces, extracts field if in parens """
        raw_string = str(raw_string).strip()
        field_extracted = None
        
        # Check for parentheses e.g., B.Tech (Computer Science)
        match = re.search(r'\((.*?)\)', raw_string)
        if match:
            field_extracted = match.group(1).strip()
            raw_string = re.sub(r'\(.*?\)', '', raw_string).strip()
            
        # Check for "in" e.g., B. Tech in CSE
        match_in = re.search(r'\bin\b(.*)', raw_string, re.IGNORECASE)
        if match_in and not field_extracted:
            field_extracted = match_in.group(1).strip()
            raw_string = raw_string[:match_in.start()].strip()
            
        cleaned = raw_string.lower().replace('.', '').replace(' (hons)', '').replace(' hons', '').strip()
        
        return cleaned, field_extracted

    def normalize_field(self, field_str):
        if not field_str: return None
        norm_field = field_str.strip().lower().replace('.', '')
        return self.field_aliases.get(norm_field, None)

    def layer1_lookup(self, cleaned):
        """ Exact dict lookup on cleaned string """
        if cleaned in self.degree_aliases:
            return {
                'canonical_degree': self.degree_aliases[cleaned],
                'confidence': 1.0,
                'status': 'resolved',
                'layer_used': 'L1'
            }
        return None

    def layer2_fuzzy(self, cleaned, threshold_auto=90, threshold_flag=75):
        """ RapidFuzz against all canonical names """
        choices = list(self.canonical_degrees)
        if not choices:
            return None
        
        result = process.extractOne(cleaned, choices, scorer=fuzz.ratio)
        if result:
            best_match, score, index = result
            # Try partial ratio and token sort ratio
            pr = fuzz.partial_ratio(cleaned, best_match)
            tsr = fuzz.token_sort_ratio(cleaned, best_match)
            score = max(score, pr, tsr)
            
            alternatives = process.extract(cleaned, choices, scorer=fuzz.ratio, limit=3)
            alt_list = [(alt[0], alt[1]) for alt in alternatives]

            if score >= threshold_auto:
                return {
                    'canonical_degree': best_match,
                    'confidence': score / 100.0,
                    'status': 'fuzzy_matched',
                    'layer_used': 'L2',
                    'fuzzy_score': score,
                    'alternatives': alt_list
                }
            elif score >= threshold_flag:
                return {
                    'canonical_degree': best_match,
                    'confidence': score / 100.0,
                    'status': 'review_needed',
                    'layer_used': 'L2',
                    'fuzzy_score': score,
                    'alternatives': alt_list
                }
        return None
        
    def layer3_stub(self, raw):
        """ Simple regex-based sentence parser for unstructured text """
        # Just a basic stub for demonstration as per instructions
        # Look for "degree in X" or "X engineering"
        if "degree in" in raw.lower() or "bachelor" in raw.lower() or "master" in raw.lower():
             return {
                 'canonical_degree': None, # We'd extract this via NER
                 'confidence': 0.5,
                 'status': 'review_needed',
                 'layer_used': 'L3_stub',
                 'fuzzy_score': 50,
                 'alternatives': []
             }
        return None

    def normalize(self, raw_string):
        cleaned, extracted_field = self.clean(raw_string)
        canonical_field = self.normalize_field(extracted_field)
        
        result = {
            'input': raw_string,
            'layer_used': 'unresolved',
            'canonical_degree': '-',
            'canonical_field': canonical_field,
            'confidence': 0.0,
            'status': 'unresolved',
            'fuzzy_score': 0,
            'alternatives': []
        }
        
        # Layer 1
        l1_res = self.layer1_lookup(cleaned)
        if l1_res:
            result.update(l1_res)
            return result
            
        # Layer 2
        l2_res = self.layer2_fuzzy(cleaned)
        if l2_res:
            result.update(l2_res)
            if l2_res['status'] != 'review_needed':
                 return result
            # If review needed, we keep it but it might be completely wrong
            # Check Layer 3 for fun if score is really low
            
        # Layer 3 (Stub)
        if not l2_res or l2_res['fuzzy_score'] < 50:
            l3_res = self.layer3_stub(raw_string)
            if l3_res:
                result.update(l3_res)
                return result
                
        # If it reached here and l2_res exists but is review_needed, return it
        if l2_res:
            return result
            
        return result

    def batch_normalize(self, list_of_strings):
        results = []
        for s in list_of_strings:
            results.append(self.normalize(s))
        return results

if __name__ == "__main__":
    import os
    
    # Needs to be run from the poc directory or adjust path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', 'data')
    
    n = Normalizer(data_dir)
    
    while True:
        print("\n" + "="*50)
        print("CV MANAGER NORMALIZATION CLI")
        print("="*50)
        print("1. Run default test cases")
        print("2. Enter custom degree string to normalize")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == '1':
            test_cases = [
                "B.Tech",
                "BTech",
                "Bachelor of Technology",
                "Bacheler of Technology",
                "B. Tech in CSE",
                "M.Tech (Computer Science)",
                "MBA",
                "Bachellor of Technolgy in CSE",
                "BE Hons",
                "12th",
                "B.Pharma",
                "Kuchh bhi degree",
            ]
            
            print(f"\nRunning normalization pipeline on {len(test_cases)} test cases...\n")
            results = n.batch_normalize(test_cases)
            
            print("-" * 64)
            print(f"{'INPUT':<30} {'CANONICAL':<25} {'LAYER':<5} {'CONF':<5} {'STATUS'}")
            print("-" * 64)
            
            stats = {'resolved_L1': 0, 'fuzzy_L2': 0, 'review': 0, 'unresolved': 0}
            review_queue = []
            
            for r in results:
                inp = r['input']
                canon = r['canonical_degree'] if r['canonical_degree'] else "-"
                layer = r['layer_used']
                conf = f"{r['confidence']:.2f}" if r['confidence'] else "-"
                status = r['status']
                
                print(f"{inp[:28]:<30} {canon[:23]:<25} {layer:<5} {conf:<5} {status}")
                if r['canonical_field']:
                    print(f"  -> field: {r['canonical_field']:<25}           L1    1.00")
                    
                if status == 'resolved' and layer == 'L1': stats['resolved_L1'] += 1
                elif status == 'fuzzy_matched' and layer == 'L2': stats['fuzzy_L2'] += 1
                elif status == 'review_needed': 
                    stats['review'] += 1
                    review_queue.append(r)
                elif status == 'unresolved': stats['unresolved'] += 1
                
            print("-" * 64 + "\n")
            
            total = len(test_cases)
            print("SUMMARY")
            print(f"  Total inputs      : {total}")
            print(f"  Resolved (L1)     : {stats['resolved_L1']}   ({(stats['resolved_L1']/total)*100:.1f}%)")
            print(f"  Fuzzy matched (L2): {stats['fuzzy_L2']}   ({(stats['fuzzy_L2']/total)*100:.1f}%)")
            print(f"  Review needed     : {stats['review']}   ({(stats['review']/total)*100:.1f}%)")
            print(f"  Unresolved        : {stats['unresolved']}   ({(stats['unresolved']/total)*100:.1f}%)\n")
            
            if review_queue:
                print("REVIEW QUEUE (items needing human attention):")
                for i, r in enumerate(review_queue, 1):
                    best_guess = r['alternatives'][0][0] if r['alternatives'] else "None"
                    score = r['fuzzy_score']
                    print(f"  {i}. \"{r['input']}\"     -> best guess: \"{best_guess}\" (score: {score:.1f})")

        elif choice == '2':
            user_input = input("\nEnter degree string (e.g., 'B.Tech (CSE)'): ").strip()
            if not user_input:
                continue
                
            r = n.normalize(user_input)
            
            print("\n" + "-" * 50)
            print("NORMALIZATION RESULT")
            print("-" * 50)
            print(f"Input            : {r['input']}")
            print(f"Canonical Degree : {r['canonical_degree'] if r['canonical_degree'] else 'None'}")
            print(f"Canonical Field  : {r['canonical_field'] if r['canonical_field'] else 'None'}")
            print(f"Layer Used       : {r['layer_used']}")
            print(f"Confidence       : {r['confidence']:.2f}")
            print(f"Status           : {r['status']}")
            
            if r['alternatives']:
                print("\nFuzzy Matching Alternatives:")
                for alt, score in r['alternatives']:
                    print(f"  - {alt} (Score: {score:.1f})")
            print("-" * 50)
            
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
