"""
CV Manager Normalizer — Sentence-Transformer Embeddings Engine (Layer 2, Engine B-3)
====================================================================================
Uses the all-MiniLM-L6-v2 model to encode degree strings into 384-dim
dense vectors. Matches input against pre-encoded reference aliases via
normalized dot product (cosine similarity).

Run:  python normalizer_embeddings.py
Note: Requires ~90 MB model download on first run.
"""

import csv
import json
import re
import os
import sys
import numpy as np

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class NormalizerEmbeddings:
    def __init__(self, data_dir='../data'):
        self.data_dir = data_dir
        self.degree_aliases = {}  # normalized -> canonical
        self.field_aliases = {}   # normalized -> canonical
        self.canonical_degrees = set()
        
        self.model = None
        self.ref_embeddings = None
        self.ref_choices = []
        
        self.load_aliases()
        self.build_embeddings_index()
        
    def load_aliases(self):
        degree_csv = os.path.join(self.data_dir, 'degree_aliases.csv')
        degree_json = os.path.join(self.data_dir, 'degree_dictionary.json')
        field_csv = os.path.join(self.data_dir, 'field_of_study_aliases.csv')
        
        if not os.path.exists(degree_csv) or not os.path.exists(field_csv):
            print("Error: Alias files not found.")
            return

        if os.path.exists(degree_json):
            with open(degree_json, 'r', encoding='utf-8') as f:
                deg_dict = json.load(f)
                for canon, data in deg_dict.items():
                    self.canonical_degrees.add(canon)
                    for alias in data['aliases']:
                        norm = self.clean_alias_string(alias)
                        self.degree_aliases[norm] = canon
        else:
            with open(degree_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.degree_aliases[row['normalized']] = row['canonical_name']
                    self.canonical_degrees.add(row['canonical_name'])
                
        with open(field_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                norm_field = row['alias'].strip().lower().replace('.', '')
                self.field_aliases[norm_field] = row['canonical_field']

        print(f"[Embeddings] Loading alias dictionary... {len(self.degree_aliases)} entries loaded.")

    def build_embeddings_index(self):
        self.ref_choices = list(self.degree_aliases.keys())
        if not self.ref_choices:
            return
            
        # Import sentence-transformers lazily to optimize imports
        from sentence_transformers import SentenceTransformer
        print("[Embeddings] Initializing all-MiniLM-L6-v2 embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Precompute reference embeddings (L2-normalized for cosine similarity via dot product)
        self.ref_embeddings = self.model.encode(
            self.ref_choices, 
            show_progress_bar=False, 
            normalize_embeddings=True
        )

    def clean_alias_string(self, raw):
        norm = raw.lower().replace('.', '').replace(' (hons)', '').replace(' hons', '').replace('-', '').replace('/', '').replace(',', '').replace('(', '').replace(')', '').strip()
        return " ".join([w for w in norm.split() if w != 'in'])

    def clean(self, raw_string):
        raw_string = str(raw_string).strip()
        field_extracted = None
        match_conn = re.split(r'\s+-\s+|\s+/\s+|\bin\b', raw_string, maxsplit=1, flags=re.IGNORECASE)
        if len(match_conn) == 2:
            raw_string = match_conn[0].strip()
            field_extracted = match_conn[1].strip()
        else:
            match = re.search(r'\((.*?)\)', raw_string)
            if match:
                field_extracted = match.group(1).strip()
                raw_string = re.sub(r'\(.*?\)', '', raw_string).strip()
            else:
                match_comma = re.split(r',', raw_string, maxsplit=1)
                if len(match_comma) == 2:
                    raw_string = match_comma[0].strip()
                    field_extracted = match_comma[1].strip()
        return self.clean_alias_string(raw_string), field_extracted

    def normalize_field(self, field_str):
        if not field_str: return None
        norm_field = field_str.strip().lower().replace('.', '')
        return self.field_aliases.get(norm_field, None)

    def layer1_lookup(self, cleaned):
        if cleaned in self.degree_aliases:
            return {
                'canonical_degree': self.degree_aliases[cleaned],
                'confidence': 1.0,
                'status': 'resolved',
                'layer_used': 'L1'
            }
        return None

    def layer2_fuzzy(self, cleaned, threshold_auto=0.75, threshold_flag=0.55):
        if not self.ref_choices or self.model is None:
            return None
            
        query_embed = self.model.encode([cleaned], normalize_embeddings=True)
        # Dot product of normalized vectors yields Cosine Similarity
        similarities = np.dot(self.ref_embeddings, query_embed.T).flatten()
        
        top_indices = np.argsort(similarities)[::-1][:5]
        if len(top_indices) == 0:
            return None
            
        best_idx = top_indices[0]
        score = float(similarities[best_idx])
        best_alias_match = self.ref_choices[best_idx]
        best_canonical = self.degree_aliases[best_alias_match]
        
        seen = {best_canonical}
        alt_list = []
        for idx in top_indices:
            alt_alias = self.ref_choices[idx]
            alt_score = float(similarities[idx])
            canon = self.degree_aliases[alt_alias]
            if canon not in seen:
                seen.add(canon)
                alt_list.append((canon, round(alt_score, 2)))
            if len(alt_list) >= 3:
                break
                
        if score >= threshold_auto:
            return {
                'canonical_degree': best_canonical,
                'confidence': round(score, 2),
                'status': 'fuzzy_matched',
                'layer_used': 'L2_Embeddings',
                'fuzzy_score': round(score * 100, 1),
                'alternatives': alt_list
            }
        elif score >= threshold_flag:
            return {
                'canonical_degree': best_canonical,
                'confidence': round(score, 2),
                'status': 'review_needed',
                'layer_used': 'L2_Embeddings',
                'fuzzy_score': round(score * 100, 1),
                'alternatives': alt_list
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
        
        l1_res = self.layer1_lookup(cleaned)
        if l1_res:
            result.update(l1_res)
            return result
            
        l2_res = self.layer2_fuzzy(cleaned)
        if l2_res:
            result.update(l2_res)
            
        return result

    def batch_normalize(self, list_of_strings):
        return [self.normalize(s) for s in list_of_strings]

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', 'data')
    n = NormalizerEmbeddings(data_dir)

    while True:
        print("\n" + "="*50)
        print("CV MANAGER NORMALIZATION CLI (Embeddings Method)")
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

            print("-" * 70)
            print(f"{'INPUT':<30} {'CANONICAL':<25} {'LAYER':<12} {'CONF':<6} {'STATUS'}")
            print("-" * 70)

            stats = {'resolved_L1': 0, 'fuzzy_L2': 0, 'review': 0, 'unresolved': 0}

            for r in results:
                inp = r['input']
                canon = r['canonical_degree'] if r['canonical_degree'] else "-"
                layer = r['layer_used']
                conf = f"{r['confidence']:.2f}" if r['confidence'] else "-"
                status = r['status']

                print(f"{inp[:28]:<30} {canon[:23]:<25} {layer:<12} {conf:<6} {status}")
                if r['canonical_field']:
                    print(f"  -> field: {r['canonical_field']:<25}")

                if status == 'resolved' and layer == 'L1': stats['resolved_L1'] += 1
                elif 'L2' in layer: stats['fuzzy_L2'] += 1
                elif status == 'review_needed': stats['review'] += 1
                elif status == 'unresolved': stats['unresolved'] += 1

            print("-" * 70 + "\n")
            total = len(test_cases)
            print("SUMMARY")
            print(f"  Total inputs      : {total}")
            print(f"  Resolved (L1)     : {stats['resolved_L1']}   ({(stats['resolved_L1']/total)*100:.1f}%)")
            print(f"  Fuzzy matched (L2): {stats['fuzzy_L2']}   ({(stats['fuzzy_L2']/total)*100:.1f}%)")
            print(f"  Review needed     : {stats['review']}   ({(stats['review']/total)*100:.1f}%)")
            print(f"  Unresolved        : {stats['unresolved']}   ({(stats['unresolved']/total)*100:.1f}%)")

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
                    print(f"  - {alt} (Score: {score})")
            print("-" * 50)

        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
