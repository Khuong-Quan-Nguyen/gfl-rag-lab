window.LAB = {
 "timestamp": "2026-11-17T14:26:43",
 "k": 10,
 "page_tolerance": 1,
 "embed_model": "sentence-transformers/all-MiniLM-L6-v2",
 "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
 "table": {
  "vector": {
   "conceptual": {
    "recall@10": 0.9,
    "top1": 0.3,
    "mrr": 0.4871428571428571,
    "n": 20
   },
   "exact": {
    "recall@10": 0.8,
    "top1": 0.6,
    "mrr": 0.64,
    "n": 20
   },
   "all": {
    "recall@10": 0.85,
    "top1": 0.45,
    "mrr": 0.5635714285714286,
    "n": 40
   },
   "p50_ms": 15.380449971416965
  },
  "hybrid": {
   "conceptual": {
    "recall@10": 0.95,
    "top1": 0.5,
    "mrr": 0.6327777777777778,
    "n": 20
   },
   "exact": {
    "recall@10": 0.9,
    "top1": 0.7,
    "mrr": 0.7641666666666667,
    "n": 20
   },
   "all": {
    "recall@10": 0.925,
    "top1": 0.6,
    "mrr": 0.6984722222222223,
    "n": 40
   },
   "p50_ms": 43.91435004072264
  },
  "vector_rerank": {
   "conceptual": {
    "recall@10": 0.95,
    "top1": 0.5,
    "mrr": 0.6529166666666667,
    "n": 20
   },
   "exact": {
    "recall@10": 0.8,
    "top1": 0.75,
    "mrr": 0.7666666666666667,
    "n": 20
   },
   "all": {
    "recall@10": 0.875,
    "top1": 0.625,
    "mrr": 0.7097916666666666,
    "n": 40
   },
   "p50_ms": 920.0449000636581
  },
  "hybrid_rerank": {
   "conceptual": {
    "recall@10": 1.0,
    "top1": 0.55,
    "mrr": 0.6813095238095238,
    "n": 20
   },
   "exact": {
    "recall@10": 0.9,
    "top1": 0.8,
    "mrr": 0.825,
    "n": 20
   },
   "all": {
    "recall@10": 0.95,
    "top1": 0.675,
    "mrr": 0.7531547619047619,
    "n": 40
   },
   "p50_ms": 944.0262000425719
  }
 },
 "latency": {
  "mode": "hybrid_rerank",
  "cold_ms": [
   8760.918900021352,
   8595.410500012804,
   8635.794000001624,
   8481.761000002734,
   8535.576599999331,
   8559.65870001819,
   9139.77079995675,
   9275.66400001524,
   8594.804299995303,
   8493.601299996953
  ],
  "warm_ms": [
   1028.6480999784544,
   949.2190999444574,
   970.8655999857001,
   932.2620999882929,
   938.5575000196695,
   1023.8900000113063,
   1024.2076000431553,
   932.8043999848887,
   924.2808000417426,
   962.2731999843381
  ],
  "p50_cold_ms": 8595.107400004053,
  "p50_warm_ms": 955.7461499643978
 },
 "questions": [
  {
   "id": "c01",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    13
   ],
   "question": "How does GFL turn gas from its landfills into a useful energy product?",
   "answer": "Biogas from decomposing MSW is collected through wells and a gas collection system and processed into RNG, used to fuel collection vehicles, generate electricity or replace natural gas for heating.",
   "ranks": {
    "vector": 2,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c02",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    14
   ],
   "question": "What is GFL's hybrid approach to setting its greenhouse gas reduction target?",
   "answer": "Three science-aligned pillars: 30% landfill emission reduction (Global Methane Assessment), 42% fleet reduction (SBTi), 100% renewable electricity (IEA net-zero), adding up to a 30% Scope 1+2 cut by 2030 vs 2021.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c03",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    11
   ],
   "question": "How does GFL help its customers improve how much waste they divert from landfill?",
   "answer": "Its Waste Audit Services Team gives customers actionable data to build diversion strategies (e.g., Fredericton's first residential waste audit).",
   "ranks": {
    "vector": null,
    "hybrid": 3,
    "vector_rerank": 5,
    "hybrid_rerank": 6
   }
  },
  {
   "id": "c04",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    11
   ],
   "question": "What does GFL's team for producer responsibility programs do?",
   "answer": "The EPR Team works with producer responsibility organizations and GFL's collection/MRF teams to turn PRO goals into operations, and educates governments on recycling strategies.",
   "ranks": {
    "vector": 2,
    "hybrid": 1,
    "vector_rerank": 2,
    "hybrid_rerank": 2
   }
  },
  {
   "id": "c05",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    12
   ],
   "question": "Why does GFL handle food scraps and yard waste separately from other garbage?",
   "answer": "Organics make up a large share of landfill waste; managed separately they become compost, mulch and soil amendments.",
   "ranks": {
    "vector": 4,
    "hybrid": null,
    "vector_rerank": 2,
    "hybrid_rerank": 6
   }
  },
  {
   "id": "c06",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    18
   ],
   "question": "How does GFL use technology to make its drivers safer?",
   "answer": "A fleet automation program reduces manual labour and flags route hazards; over 65% of solid waste vehicles have cameras used for driver coaching.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c07",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    16
   ],
   "question": "How does GFL turn employee ideas into sustainability projects, and which areas does it prioritize?",
   "answer": "The Environmental Innovation Program turns ideas into Sustainability Value Initiatives; priorities: landfill fugitive emissions, customer scope 3 pilots, advanced material recovery, zero-emission vehicle pilots.",
   "ranks": {
    "vector": 5,
    "hybrid": 3,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c08",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    20
   ],
   "question": "How is GFL supporting the education of its employees and their children?",
   "answer": "Greenleaf Scholars Program for dependents, Green Futures Employee Scholarship (up to $40,000/year), and the GFL Learning Hub.",
   "ranks": {
    "vector": 1,
    "hybrid": 2,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c09",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    19
   ],
   "question": "What did GFL change after listening to feedback from its workforce?",
   "answer": "Quarterly recognition programs, regional town halls and newsletters, expanded leadership development and structured focus groups.",
   "ranks": {
    "vector": 3,
    "hybrid": 6,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c10",
   "type": "conceptual",
   "doc": "sustainability_2024",
   "pages": [
    24
   ],
   "question": "How has GFL helped communities recover after storms and hurricanes?",
   "answer": "Managed storm debris in southern Texas at its landfills (Fort Bend) and employees collected supplies for Hurricane Helene victims.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c11",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    47,
    96
   ],
   "question": "What is GFL's overall strategy for growing the business?",
   "answer": "Three-pronged: strong stable organic revenue growth, strategic accretive acquisitions, and operating cost efficiencies.",
   "ranks": {
    "vector": 5,
    "hybrid": 9,
    "vector_rerank": 8,
    "hybrid_rerank": 7
   }
  },
  {
   "id": "c12",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    47
   ],
   "question": "Why does GFL give regional leaders oversight of operations instead of centralizing control?",
   "answer": "A decentralized structure suits regional, fragmented markets and relationship-based acquisitions, and gives employees a sense of ownership.",
   "ranks": {
    "vector": 5,
    "hybrid": 10,
    "vector_rerank": 3,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c13",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    50
   ],
   "question": "How do transfer stations help GFL keep costs down?",
   "answer": "Internalizing waste avoids third-party disposal fees and consolidating volumes reduces transport costs to landfills.",
   "ranks": {
    "vector": 2,
    "hybrid": 1,
    "vector_rerank": 2,
    "hybrid_rerank": 2
   }
  },
  {
   "id": "c14",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    50
   ],
   "question": "How do GFL's recycling sorting facilities make money?",
   "answer": "Mostly processing fees charged on volume received, plus sales of recyclable materials to third parties.",
   "ranks": {
    "vector": 7,
    "hybrid": 2,
    "vector_rerank": 5,
    "hybrid_rerank": 5
   }
  },
  {
   "id": "c15",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    48
   ],
   "question": "How does GFL find, close and integrate the companies it buys?",
   "answer": "Platform acquisitions of premier regional operators then tuck-ins; local pipeline via decentralized structure; due diligence, definitive agreement, then integration; reputation as acquirer-of-choice.",
   "ranks": {
    "vector": null,
    "hybrid": 9,
    "vector_rerank": null,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c16",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    33
   ],
   "question": "What kinds of cyber threats could hurt GFL's business?",
   "answer": "State-sponsored actors, hackers, hacktivists; phishing, ransomware, insider malfeasance, vulnerable software; third-party breaches; data breach liability and reputational harm.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c17",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    30
   ],
   "question": "How could government efforts to reduce landfilling affect GFL?",
   "answer": "Landfills could run at reduced capacity or GFL could be forced to charge lower rates, due to source reduction, recycling mandates, disposal bans and capacity limits.",
   "ranks": {
    "vector": 3,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 4
   }
  },
  {
   "id": "c18",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    49
   ],
   "question": "How are prices set and adjusted in GFL's contracts with municipalities?",
   "answer": "Fees per volume, household, service or lift; annual price adjustments tied to indices like CPI plus fuel adjustments; terms of 3-10 years with renewals.",
   "ranks": {
    "vector": 3,
    "hybrid": 1,
    "vector_rerank": 2,
    "hybrid_rerank": 2
   }
  },
  {
   "id": "c19",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    49
   ],
   "question": "What is the purpose of GFL's renewable energy subsidiary?",
   "answer": "GFL Renewables (formed 2021) develops RNG, renewable electricity, wind and solar projects at GFL landfills.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "c20",
   "type": "conceptual",
   "doc": "annual_report_2024",
   "pages": [
    51
   ],
   "question": "What services does GFL's liquid waste business provide?",
   "answer": "Collection, transport and processing of hazardous and non-hazardous liquid waste, on-site industrial cleaning, UMO resale and 24/7 HAZMAT emergency response.",
   "ranks": {
    "vector": 4,
    "hybrid": 2,
    "vector_rerank": 5,
    "hybrid_rerank": 5
   }
  },
  {
   "id": "e01",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    13,
    7
   ],
   "question": "How many MMBtu of landfill gas did GFL produce for beneficial use in 2024?",
   "answer": "More than 4.5 million MMBtu.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e02",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    10
   ],
   "question": "What total tonnage of recyclables did GFL MRFs recover in 2024?",
   "answer": "1,267,279 tonnes (more than 1.2 million).",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e03",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    10
   ],
   "question": "What is the annual capacity of the Montreal-Est MRF and how many optical sorters does it use?",
   "answer": "Up to 200,000 tonnes per year; 17 AI-powered optical sorters; 52 tonnes per hour.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e04",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    13
   ],
   "question": "How many homes can the RNG from the facility southeast of Kansas City, Missouri power?",
   "answer": "7,200 homes (equivalent to removing 17,500 cars).",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e05",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    15
   ],
   "question": "What percentage of GFL's U.S. CNG fleet runs on RNG, and what is the 2030 goal?",
   "answer": "More than 72%; goal 85% by 2030.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e06",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    14
   ],
   "question": "How much electricity did the East Mount Hauling Yard lighting retrofit in Houston save?",
   "answer": "62%, about 78,000 kWh annually (260+ fixtures replaced).",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e07",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    22,
    4
   ],
   "question": "How much did GFL invest through the Full Circle Project in 2024?",
   "answer": "Over $4.2 million in 220+ projects across 105 branch locations ($1.5M FCP Today + $2.7M FCP Tomorrow).",
   "ranks": {
    "vector": 5,
    "hybrid": 2,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e08",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    15,
    8
   ],
   "question": "How many Tier 1 supplier sustainability audits had GFL completed by the end of 2024?",
   "answer": "32 of the 100 planned.",
   "ranks": {
    "vector": 5,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e09",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    25
   ],
   "question": "Which GFL landfill earned Gold Certification for its biodiversity program?",
   "answer": "Mallard Ridge Landfill in Delavan, Wisconsin.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e10",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    19
   ],
   "question": "What was GFL's voluntary turnover rate in 2024 and its target for 2028?",
   "answer": "Just above 20%; goal of mid-teens by 2028.",
   "ranks": {
    "vector": 1,
    "hybrid": 3,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e11",
   "type": "exact",
   "doc": "sustainability_2024",
   "pages": [
    19
   ],
   "question": "What share of employees took part in GFL's first employee experience survey?",
   "answer": "63%.",
   "ranks": {
    "vector": 5,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e12",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    98,
    46
   ],
   "question": "What was GFL's Landfill revenue for fiscal 2024?",
   "answer": "$1,088.8 million (13.8% of revenue, up 15.8%).",
   "ranks": {
    "vector": null,
    "hybrid": 4,
    "vector_rerank": null,
    "hybrid_rerank": 6
   }
  },
  {
   "id": "e13",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    97,
    2
   ],
   "question": "What was GFL's Adjusted EBITDA for the year ended December 31, 2024?",
   "answer": "$2,250.5 million (up 12.3%).",
   "ranks": {
    "vector": 1,
    "hybrid": null,
    "vector_rerank": null,
    "hybrid_rerank": null
   }
  },
  {
   "id": "e14",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    3,
    50
   ],
   "question": "At what enterprise value was the Environmental Services business sold, and what cash did GFL receive?",
   "answer": "$8.0 billion enterprise value; about $6.2 billion cash proceeds; effective March 1, 2025.",
   "ranks": {
    "vector": 5,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e15",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    48,
    96
   ],
   "question": "How many acquisitions has GFL completed since it began operations in 2007?",
   "answer": "Over 270.",
   "ranks": {
    "vector": null,
    "hybrid": 5,
    "vector_rerank": null,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e16",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    52
   ],
   "question": "What percentage of GFL's employees are unionized?",
   "answer": "10.4% (of ~20,000 employees; 52.2% in Canada).",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e17",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    62
   ],
   "question": "Where is GFL's head office and how much space does it lease?",
   "answer": "Vaughan, Ontario; about 66,000 square feet, lease expiring 2028.",
   "ranks": {
    "vector": null,
    "hybrid": null,
    "vector_rerank": null,
    "hybrid_rerank": null
   }
  },
  {
   "id": "e18",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    120
   ],
   "question": "What was GFL's average landfill amortization per tonne in 2024?",
   "answer": "$14.1 per tonne (22.7 million tonnes received).",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e19",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    58
   ],
   "question": "What Maximum Contaminant Level did the EPA set for PFOA and PFOS in drinking water?",
   "answer": "4.0 parts per trillion.",
   "ranks": {
    "vector": 1,
    "hybrid": 1,
    "vector_rerank": 1,
    "hybrid_rerank": 1
   }
  },
  {
   "id": "e20",
   "type": "exact",
   "doc": "annual_report_2024",
   "pages": [
    99
   ],
   "question": "How much did GFL spend on fuel in cost of sales in 2024?",
   "answer": "$332.8 million, down $41.9 million (11.2%).",
   "ranks": {
    "vector": null,
    "hybrid": 1,
    "vector_rerank": 3,
    "hybrid_rerank": 3
   }
  }
 ]
};
