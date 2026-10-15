"""Curated 15-book seed dataset across all four physical inventory lifecycle states.

States:
- 6 AVAILABLE (ready for immediate checkout)
- 4 CHECKED_OUT (3 active, 1 overdue)
- 3 IN_PROCESSING (returned items awaiting librarian triage/reshelving)
- 2 IN_MAINTENANCE (flagged with physical damage for reverse logistics triage)
"""

from typing import Any

SEED_BOOKS: list[dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. AVAILABLE BOOKS (6)
    # -------------------------------------------------------------------------
    {
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "isbn": "978-1449373320",
        "genre": "Distributed Systems",
        "publication_year": 2017,
        "dewey_decimal": "005.74",
        "summary": (
            "An indispensable guide to the principles and architectures underpinning modern "
            "data-intensive systems. Examines distributed transactions, consensus protocols, "
            "partitioning, replication, stream processing, and consistency models with deep "
            "engineering rigor.\n\n"
            "Essential reading for software architects and senior backend engineers aiming to "
            "evaluate storage engines, batch processing frameworks, and high-throughput databases."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781449373320-L.jpg",
        "status": "AVAILABLE",
    },
    {
        "title": "Clean Architecture: A Craftsman's Guide to Software Structure",
        "author": "Robert C. Martin",
        "isbn": "978-0134494166",
        "genre": "Software Architecture",
        "publication_year": 2017,
        "dewey_decimal": "005.1",
        "summary": (
            "A definitive exploration of practical software architecture rules and principles. "
            "Presents the Dependency Inversion Principle, Component Cohesion, and boundary "
            "enforcement between core business entities and external delivery mechanisms like "
            "databases and user interfaces.\n\n"
            "Provides clear blueprints for structuring maintainable, testable, and loosely "
            "coupled enterprise applications resilient to infrastructure changes."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780134494166-L.jpg",
        "status": "AVAILABLE",
    },
    {
        "title": "The Pragmatic Programmer: Your Journey To Mastery",
        "author": "David Thomas, Andrew Hunt",
        "isbn": "978-0135957059",
        "genre": "Software Engineering",
        "publication_year": 2019,
        "dewey_decimal": "005.1",
        "summary": (
            "A timeless collection of insights, practical philosophies, and craftsmanship habits "
            "for professional software engineers. Explores defensive programming, domain "
            "prototyping, contract-driven design, and the discipline of continuous refactoring.\n\n"
            "This 20th Anniversary Edition modernizes classic guidance for concurrent computing, "
            "team organization, and personal career longevity in technology."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780135957059-L.jpg",
        "status": "AVAILABLE",
    },
    {
        "title": "Database Internals: A Deep Dive into Distributed Systems",
        "author": "Alex Petrov",
        "isbn": "978-1492040347",
        "genre": "Database Systems",
        "publication_year": 2019,
        "dewey_decimal": "005.74",
        "summary": (
            "An exhaustive technical deep dive into modern storage engines and distributed "
            "database internals. Contrasts B-Tree family storage with Log-Structured Merge (LSM) "
            "trees, write-ahead logs, and memory management subsystems.\n\n"
            "Covers leaderless versus leader-based consensus, replication mechanics, and two-phase "
            "commit algorithms powering modern relational and NewSQL database architectures."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781492040347-L.jpg",
        "status": "AVAILABLE",
    },
    {
        "title": "Site Reliability Engineering: How Google Runs Production Systems",
        "author": "Betsy Beyer, Chris Jones, Jennifer Petoff, Niall Murphy",
        "isbn": "978-1491929124",
        "genre": "DevOps & Reliability",
        "publication_year": 2016,
        "dewey_decimal": "005.1",
        "summary": (
            "A groundbreaking collection of essays and operational post-mortems from Google's "
            "Site Reliability Engineering (SRE) team. Defines service level objectives (SLOs), "
            "error budgets, blameless post-mortem culture, and distributed telemetry.\n\n"
            "Demonstrates how treating operations as a software engineering discipline unlocks "
            "unprecedented reliability and velocity across massive planetary-scale infrastructure."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781491929124-L.jpg",
        "status": "AVAILABLE",
    },
    {
        "title": "Building Microservices: Designing Fine-Grained Systems",
        "author": "Sam Newman",
        "isbn": "978-1492034025",
        "genre": "Microservices & Cloud",
        "publication_year": 2021,
        "dewey_decimal": "005.133",
        "summary": (
            "A comprehensive architectural handbook for planning, decomposing, and operating "
            "microservice architectures. Evaluates asynchronous message brokering versus gRPC, "
            "distributed authentication patterns, and database decomposition strategies.\n\n"
            "Includes pragmatic guidelines for service observability, container orchestration, "
            "and continuous deployment pipelines in high-concurrency environments."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781492034025-L.jpg",
        "status": "AVAILABLE",
    },

    # -------------------------------------------------------------------------
    # 2. CHECKED_OUT BOOKS (4: 3 Active, 1 Overdue)
    # -------------------------------------------------------------------------
    {
        "title": "System Design Interview – An Insider's Guide",
        "author": "Alex Xu",
        "isbn": "979-8664653403",
        "genre": "System Design",
        "publication_year": 2020,
        "dewey_decimal": "004.2",
        "summary": (
            "A visual, step-by-step masterclass on architecting scalable distributed systems "
            "capable of serving millions of concurrent global users. Deconstructs rate limiters, "
            "consistent hashing rings, distributed message queues, and notification platforms.\n\n"
            "Features real-world architectural case studies analyzing YouTube video ingestion, "
            "Google Drive sync protocols, and Twitter feed generation."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9798664653403-L.jpg",
        "status": "CHECKED_OUT",
        "is_overdue": False,
    },
    {
        "title": "Refactoring: Improving the Design of Existing Code",
        "author": "Martin Fowler",
        "isbn": "978-0134757599",
        "genre": "Software Engineering",
        "publication_year": 2018,
        "dewey_decimal": "005.1",
        "summary": (
            "The classic catalog of code smells and step-by-step refactoring transformations. "
            "Demonstrates how incremental design improvements supported by robust unit test suites "
            "drastically improve code readability, reduce defect rates, and eliminate technical debt.\n\n"
            "Fully revised with modern examples highlighting functional programming idioms and "
            "composability."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780134757599-L.jpg",
        "status": "CHECKED_OUT",
        "is_overdue": False,
    },
    {
        "title": "Kubernetes: Up and Running",
        "author": "Kelsey Hightower, Brendan Burns, Joe Beda",
        "isbn": "978-1492046530",
        "genre": "Cloud Infrastructure",
        "publication_year": 2019,
        "dewey_decimal": "005.1",
        "summary": (
            "Written by core creators of the Kubernetes container orchestrator, this book demystifies "
            "pod lifecycles, declarative replica sets, ingress controllers, and horizontal auto-scaling.\n\n"
            "Provides production-grade patterns for continuous deployment, stateful sets, storage volumes, "
            "and service discovery across multi-cloud clusters."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781492046530-L.jpg",
        "status": "CHECKED_OUT",
        "is_overdue": False,
    },
    {
        "title": "Computer Networking: A Top-Down Approach",
        "author": "James Kurose, Keith Ross",
        "isbn": "978-0132856201",
        "genre": "Computer Networks",
        "publication_year": 2012,
        "dewey_decimal": "004.6",
        "summary": (
            "A foundational textbook structuring computer network protocols from application-layer "
            "HTTP, DNS, and TLS down through transport layer TCP/UDP congestion controls, BGP routing, "
            "and wireless link layers.\n\n"
            "Features comprehensive packet inspection exercises and rigorous mathematical analyses of "
            "packet queuing latency and throughput bounds."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780132856201-L.jpg",
        "status": "CHECKED_OUT",
        "is_overdue": True,  # Seeded with a past due date to demonstrate OVERDUE badge calculation
    },

    # -------------------------------------------------------------------------
    # 3. IN_PROCESSING BOOKS (3)
    # -------------------------------------------------------------------------
    {
        "title": "Introduction to Algorithms",
        "author": "Thomas H. Cormen, Charles Leiserson, Ronald Rivest, Clifford Stein",
        "isbn": "978-0262046305",
        "genre": "Algorithms & Data Structures",
        "publication_year": 2022,
        "dewey_decimal": "005.1",
        "summary": (
            "The globally recognized CLRS bible of algorithmic computer science. Provides rigorous "
            "mathematical proofs and pseudocode for dynamic programming, divide-and-conquer recurrences, "
            "graph traversals, maximum flow, and NP-completeness.\n\n"
            "The fourth edition incorporates modern treatments of bipartite matching, online algorithms, "
            "and machine learning data structures."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780262046305-L.jpg",
        "status": "IN_PROCESSING",
    },
    {
        "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
        "author": "Robert C. Martin",
        "isbn": "978-0132350884",
        "genre": "Software Engineering",
        "publication_year": 2008,
        "dewey_decimal": "005.1",
        "summary": (
            "An enduring classic establishing industry standards for meaningful variable naming, "
            "function atomicity, error handling, and test-driven development (TDD).\n\n"
            "Includes extensive case studies examining source code transformations that convert "
            "fragile legacy routines into clean, maintainable, and self-documenting modules."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780132350884-L.jpg",
        "status": "IN_PROCESSING",
    },
    {
        "title": "Operating Systems: Three Easy Pieces",
        "author": "Remzi H. Arpaci-Dusseau, Andrea C. Arpaci-Dusseau",
        "isbn": "978-1985086593",
        "genre": "Operating Systems",
        "publication_year": 2018,
        "dewey_decimal": "005.43",
        "summary": (
            "A remarkably accessible, foundational text dissecting modern operating system concepts "
            "around three central pillars: Virtualization (CPU and memory), Concurrency (threads, "
            "locks, semaphores), and Persistence (file systems, SSD flash management, and crash recovery).\n\n"
            "Packed with operational C code examples demonstrating low-level kernel mechanics."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781985086593-L.jpg",
        "status": "IN_PROCESSING",
    },

    # -------------------------------------------------------------------------
    # 4. IN_MAINTENANCE BOOKS (2)
    # -------------------------------------------------------------------------
    {
        "title": "Structure and Interpretation of Computer Programs",
        "author": "Harold Abelson, Gerald Jay Sussman",
        "isbn": "978-0262510875",
        "genre": "Programming Languages",
        "publication_year": 1996,
        "dewey_decimal": "005.133",
        "summary": (
            "The iconic SICP text from MIT that transformed how computer scientists conceptualize "
            "abstraction, higher-order procedures, lexical scoping, and meta-linguistic abstraction.\n\n"
            "Explores register machines, garbage collection internals, and evaluator implementations "
            "that form the bedrock of programming language theory."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780262510875-L.jpg",
        "status": "IN_MAINTENANCE",
        "initial_damage_note": (
            "Spine adhesive cracked along the central signatures; front endpaper loose and detached "
            "from binding hinge. Requires archival PVA adhesive re-gluing and binding press clamp."
        ),
    },
    {
        "title": "Pattern Recognition and Machine Learning",
        "author": "Christopher M. Bishop",
        "isbn": "978-0387310732",
        "genre": "Machine Learning",
        "publication_year": 2006,
        "dewey_decimal": "006.31",
        "summary": (
            "The definitive graduate-level treatment of Bayesian pattern recognition, graphical models, "
            "variational inference, and kernel methods.\n\n"
            "Provides unified mathematical derivations for expectation maximization, hidden Markov models, "
            "and statistical decision theory powering contemporary machine learning systems."
        ),
        "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780387310732-L.jpg",
        "status": "IN_MAINTENANCE",
        "initial_damage_note": (
            "Liquid spill staining across lower corner of pages 14 through 28 causing warped page margins. "
            "Pages remain legible; requires desiccant blotter drying and fungal disinfection review."
        ),
    },
]

