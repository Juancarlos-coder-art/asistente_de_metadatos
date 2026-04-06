from urllib.parse import unquote
import logging

from rdflib import BNode, DCAT, Literal, RDF, RDFS, URIRef, XSD
from rdflib.namespace import DCTERMS as DCT
from rdflib.namespace import FOAF, Namespace, OWL, SKOS

from ckanext.dcat.profiles.base import CleanedURIRef
from ckanext.dcat.profiles.euro_dcat_ap_3 import EuropeanDCATAP3Profile
from ckanext.dcat.utils import resource_uri

log = logging.getLogger(__name__)


HEALTHDCATAP = Namespace("http://healthdataportal.eu/ns/health#")
DPV = Namespace("https://w3id.org/dpv#")
PD = Namespace("https://w3id.org/dpv/pd#")
DQV = Namespace("http://www.w3.org/ns/dqv#")
OA = Namespace("http://www.w3.org/ns/oa#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
CV = Namespace("http://data.europa.eu/m8g/")
DCATAP = Namespace("http://data.europa.eu/r5r/")
ELI = Namespace("http://data.europa.eu/eli/ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")
TIME = Namespace("http://www.w3.org/2006/time#")


CONCEPT_SCHEME_RULES = (
    {
        "prefix": "http://publications.europa.eu/resource/authority/language/",
        "class": DCT.LinguisticSystem,
        "scheme": URIRef("http://publications.europa.eu/resource/authority/language"),
        "labels": {
            "BUL": "Bulgarian",
            "CES": "Czech",
            "DAN": "Danish",
            "DEU": "German",
            "ELL": "Greek",
            "ENG": "English",
            "EST": "Estonian",
            "FIN": "Finnish",
            "FRA": "French",
            "GLE": "Irish",
            "HRV": "Croatian",
            "HUN": "Hungarian",
            "ITA": "Italian",
            "LAV": "Latvian",
            "LIT": "Lithuanian",
            "MLT": "Maltese",
            "NLD": "Dutch",
            "POL": "Polish",
            "POR": "Portuguese",
            "RON": "Romanian",
            "SLK": "Slovak",
            "SLV": "Slovenian",
            "SPA": "Spanish",
            "SWE": "Swedish",
        },
    },
    {
        "prefix": "http://publications.europa.eu/resource/authority/access-right/",
        "class": DCT.RightsStatement,
        "scheme": URIRef("http://publications.europa.eu/resource/authority/access-right"),
        "labels": {
            "PUBLIC": "Public",
            "RESTRICTED": "Restricted",
            "NON_PUBLIC": "Non-public",
        },
    },
    {
        "prefix": "http://publications.europa.eu/resource/authority/frequency/",
        "class": DCT.Frequency,
        "scheme": URIRef("http://publications.europa.eu/resource/authority/frequency"),
        "labels": {
            "ANNUAL": "Annual",
            "BIENNIAL": "Biennial",
            "MONTHLY_2": "Semimonthly",
            "BIMONTHLY": "Bimonthly",
            "WEEKLY_2": "Semiweekly",
            "QUINQUENNIAL": "Quinquennial",
            "5MIN": "Every five minutes",
            "QUADRENNIAL": "Quadrennial",
            "DECENNIAL": "Decennial",
            "10MIN": "Every ten minutes",
            "12HRS": "Every twelve hours",
            "BIHOURLY": "Bihourly",
            "HOURLY": "Hourly",
            "1MIN": "Every minute",
            "15MIN": "Every fifteen minutes",
            "TRIDECENNIAL": "Tridecennial",
            "30MIN": "Every thirty minutes",
            "TRIHOURLY": "Trihourly",
            "BIDECENNIAL": "Bidecennial",
            "WEEKLY_5": "Five times a week",
            "UPDATE_CONT": "Continuously updated",
            "CONT": "Continuous",
            "ANNUAL_3": "Three times a year",
            "OP_DATPRO": "Provisional data",
            "UNKNOWN": "Unknown",
            "DAILY": "Daily",
            "DAILY_2": "Twice a day",
            "AS_NEEDED": "As needed",
            "IRREG": "Irregular",
            "MONTHLY": "Monthly",
            "NOT_PLANNED": "Not planned",
            "NEVER": "Never",
            "OTHER": "Other",
            "BIWEEKLY": "Biweekly",
            "WEEKLY": "Weekly",
            "ANNUAL_2": "Semiannual",
            "SEXENNIAL": "Sexennial",
            "MONTHLY_3": "Three times a month",
            "WEEKLY_3": "Three times a week",
            "TRIENNIAL": "Triennial",
            "QUARTERLY": "Quarterly",
        },
    },
    {
        "prefix": "http://publications.europa.eu/resource/authority/file-type/",
        "class": DCT.MediaTypeOrExtent,
        "scheme": URIRef("http://publications.europa.eu/resource/authority/file-type"),
        "labels": {
            "CSV": "CSV",
            "JSON": "JSON",
            "PDF": "PDF",
            "RDF": "RDF",
            "TXT": "TXT",
            "XML": "XML",
            "XLS": "XLS",
            "XLSX": "XLSX",
            "ZIP": "ZIP",
        },
    },
    {
        "prefix": "http://publications.europa.eu/resource/authority/dataset-type/",
        "class": None,
        "scheme": URIRef("http://publications.europa.eu/resource/authority/dataset-type"),
        "labels": {
            "RELEASE": "Release",
            "SERIES": "Series",
            "SERVICE": "Service",
        },
    },
    {
        "prefix": "http://publications.europa.eu/resource/authority/data-theme/",
        "class": None,
        "scheme": URIRef("http://publications.europa.eu/resource/authority/data-theme"),
        "labels": {
            "HEAL": "Health",
            "TECH": "Science and technology",
        },
    },
    {
        "prefix": "http://13.81.34.152:1101/resource/authority/health-theme/",
        "class": None,
        "scheme": URIRef("http://13.81.34.152:1101/resource/authority/health-theme"),
        "labels": {
            "ANTIMICROBIAL_CONTROL": "Antimicrobial resistance & infection control",
            "TROPICAL_DISEASES": "Tropical diseases",
        },
    },
    {
        "prefix": "http://13.81.34.152:1101/resource/authority/healthcategories/",
        "class": None,
        "scheme": URIRef("http://13.81.34.152:1101/resource/authority/healthcategories"),
        "labels": {
            "RPDG": "Data on pathogens that impact human health",
            "RMMD": "Data from registries for medicinal products and medical devices",
        },
    },

    {
        "prefix": "http://13.81.34.152:1101/resource/authority/health-activity/",
        "class": None,
        "scheme": URIRef("http://13.81.34.152:1101/resource/authority/health-activity"),
        "labels": {
            "EHEALTH_APPLICATION": "eHealth application",
            "NONMEDICAL_APPLICATION": "Non-medical application",
            "HOSPITAL_RECORDS": "Hospital records database",
            "RESEARCH_DATABASE": "Dedicated research database",
            "BIOBANK_COLLECTION": "Biobank/sample collection",
            "COHORT": "Cohort",
            "SAMPLE_COLLECTIONS": "Sample collections",
            "OBSERVATIONAL_DATA": "Observational Data",
            "CENSUS_DATA": "Census data",
            "PROBABILITY_SURVEY": "Probability survey",
            "HEALTH_SURVEY": "Health survey",
            "CLINICAL_TRIAL": "Clinical trial",
            "AUTOMATIC_GENERATION": "Automatically generated",
            "ADMISSION_DISCHARGE": "Patient admission, care and discharge",
            "MEASUREMENTS": "Measurements",
            "MODELS_SIMULATIONS": "Models and simulations",
            "PRESCRIBING_DISPENSING": "Prescribing or dispensing medicines",
            "ADMINISTRATIVE_PROCESSES": "Administrative processes",
            "PATIENT_OUTCOMES": "PROM (Patient-Reported Outcome Measures)",
            "RESEARCH_PROJECT": "Research project",
            "LABORATORY_TESTS": "Laboratory tests",
            "INSURANCE_CLAIMS": "Claims, insurances and reimbursement",
            "QUALITY_REGISTRY": "Quality Registry",
            "MEDICAL_REGISTRY": "Medical registry",
            "ROUTINE_RECORDS": "Routine records (non-health)",
            "QUALITY_REGISTRIES": "National Medical Quality Registries",
            "HEALTH_REGISTRIES": "National Health Registries",
            "MUNICIPAL_REPOSITORY": "Municipal health data repository",
            "GEOSPATIAL_MONITORING": "Geospatial monitoring",
            "MEDICAL_DEVICES": "Use of medical devices",
            "SURVEILLANCE": "Surveillance",
            "DISEASE_MONITORING": "Infectious disease monitoring",
            "HEALTH_SURVEILLANCE": "Public Health Surveillance",
            "HEALTHCARE_VISIT": "Healthcare visit",
        },
    },
    {
        "prefix": "http://13.81.34.152:1101/resource/authority/publisher-type/",
        "class": None,
        "scheme": URIRef("http://13.81.34.152:1101/resource/authority/publisher-type"),
        "labels": {
            "research-academic-org": "Research and academic organisation",
        },
    },
    {
        "prefix": "http://publications.europa.eu/resource/authority/corporate-body/",
        "class": None,
        "scheme": URIRef("http://publications.europa.eu/resource/authority/corporate-body"),
        "labels": {
            "EURUN": "European Union",
        },
    },
    {
        "prefix": "https://www.iana.org/assignments/media-types/",
        "class": DCT.MediaType,
        "scheme": URIRef("https://www.iana.org/assignments/media-types/"),
        "labels": {},
    },
)


class EuropeanHealthDCATAPProfile(EuropeanDCATAP3Profile):
    def parse_dataset(self, dataset_dict, dataset_ref):
        dataset_dict = super(EuropeanHealthDCATAPProfile, self).parse_dataset(
            dataset_dict, dataset_ref
        )
        self._bind_namespaces()
        self._parse_health_fields(dataset_dict, dataset_ref)
        self._normalize_applicable_legislation_fields(dataset_dict)
        self._normalize_conforms_to_field(dataset_dict, dataset_ref)
        self._normalize_documentation_field(dataset_dict, dataset_ref)
        self._normalize_coding_system_field(dataset_dict, dataset_ref)
        self._normalize_landing_page_field(dataset_dict, dataset_ref)
        self._normalize_multi_uri_choice_field(dataset_dict, dataset_ref, "language", DCT.language)
        self._normalize_multi_uri_choice_field(dataset_dict, dataset_ref, "theme", DCAT.theme)
        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        super().graph_from_dataset(dataset_dict, dataset_ref)
        self._bind_namespaces()

        self._remove_predicate_objects(dataset_ref, DCT.publisher)
        self._remove_predicate_objects(dataset_ref, DCT.creator)
        self._remove_predicate_objects(dataset_ref, HEALTHDCATAP.hdab)
        self._remove_predicate_objects(dataset_ref, DCATAP.applicableLegislation)
        self._remove_predicate_objects(dataset_ref, DPV.hasLegalBasis)
        self._remove_predicate_objects(dataset_ref, DCT.relation)
        self._remove_predicate_objects(dataset_ref, PROV.qualifiedAttribution)

        self._fix_spatial(dataset_dict, dataset_ref)
        self._fix_dataset_concepts(dataset_dict, dataset_ref)
        self._remove_predicate_objects(dataset_ref, DCT.hasVersion)
        self._remove_predicate_objects(dataset_ref, DCT.isVersionOf)
        self._add_conforms_to_values(dataset_dict, dataset_ref)
        self._add_documentation_values(dataset_dict, dataset_ref)
        self._add_landing_page_values(dataset_dict, dataset_ref)

        self._add_health_dataset_fields(dataset_dict, dataset_ref)
        self._declare_health_concept_schemes()
        log.debug("[healthdcatap][graph_from_dataset:agents_input] publisher=%r creator=%r hdab=%r", dataset_dict.get("publisher"), dataset_dict.get("creator"), dataset_dict.get("hdab"))
        self._add_health_agents(dataset_ref, dataset_dict)
        self._add_dataset_contact_points(dataset_ref, dataset_dict.get("contact"))
        self._add_quality_annotation(dataset_dict, dataset_ref)
        self._add_retention_period(dataset_ref, dataset_dict.get("retention_period", []))
        
        dataset_legislation = self._normalize_uri_list(
            self._get_dict_value(dataset_dict, "applicable_legislation") or []
        )

        for leg in dataset_legislation:
            if self._is_uri(leg):
                leg_ref = URIRef(leg)
                self.g.add((dataset_ref, DCATAP.applicableLegislation, leg_ref))
                self.g.add((leg_ref, RDF.type, ELI.LegalResource))

        self._add_related_resource_values(dataset_dict, dataset_ref)
        self._add_qualified_attributions(dataset_ref, dataset_dict.get("qualified_attribution", []))

        for resource_dict in dataset_dict.get("resources", []):
            distribution_ref = CleanedURIRef(resource_uri(resource_dict))
            self._remove_predicate_objects(distribution_ref, DCATAP.applicableLegislation)
            self._add_retention_period(
                distribution_ref,
                resource_dict.get("retention_period", []),
            )

            resource_legislation = self._normalize_uri_list(
                resource_dict.get("applicable_legislation") or []
            )
            legislation_values = resource_legislation or dataset_legislation
            for leg in legislation_values:
                if self._is_uri(leg):
                    leg_ref = URIRef(leg)
                    self.g.add((distribution_ref, DCATAP.applicableLegislation, leg_ref))
                    self.g.add((leg_ref, RDF.type, ELI.LegalResource))

            self._fix_distribution_concepts(resource_dict, distribution_ref)

    def _declare_health_concept_schemes(self):
        schemes = (
            (
                URIRef("http://13.81.34.152:1101/resource/authority/health-theme"),
                "Health theme",
            ),
            (
                URIRef("http://13.81.34.152:1101/resource/authority/healthcategories"),
                "Health categories",
            ),
            (
                URIRef("http://13.81.34.152:1101/resource/authority/health-activity"),
                "Health activity",
            ),
        )

        for scheme_ref, label in schemes:
            self.g.add((scheme_ref, RDF.type, SKOS.ConceptScheme))
            self.g.add((scheme_ref, DCT.title, Literal(label, lang="en")))
            self.g.add((scheme_ref, SKOS.prefLabel, Literal(label, lang="en")))

    def _parse_health_fields(self, dataset_dict, dataset_ref):
        self.__parse_healthdcat_stringvalues(dataset_dict, dataset_ref)
        self.__parse_healthdcat_booleanvalues(dataset_dict, dataset_ref)
        self.__parse_healthdcat_intvalues(dataset_dict, dataset_ref)

        temporal_resolution = self._object_value(dataset_ref, DCAT.temporalResolution)
        if temporal_resolution:
            dataset_dict["temporal_resolution"] = temporal_resolution

        spatial_values = self._parse_spatial_values(dataset_ref)
        if spatial_values:
            dataset_dict["spatial"] = spatial_values
            log.debug("[healthdcatap][parsed_spatial_into_dataset] %r", spatial_values)

        related_values = []
        for obj in self.g.objects(dataset_ref, DCT.relation):
            if isinstance(obj, URIRef):
                related_values.append({
                    "uri": str(obj),
                    "label": self._object_value(obj, RDFS.label) or "",
                })

        if related_values:
            dataset_dict["related_resource"] = related_values

        qualified_attributions = self._parse_qualified_attributions(dataset_ref)
        if qualified_attributions:
            dataset_dict["qualified_attribution"] = qualified_attributions

        publishers = self._parse_agents_with_contact_point(dataset_ref, DCT.publisher)
        if publishers:
            dataset_dict["publisher"] = publishers
            log.debug("[healthdcatap][parsed_publishers] %r", publishers)

        creators = self._parse_agents_with_contact_point(dataset_ref, DCT.creator)
        if creators:
            dataset_dict["creator"] = creators
            log.debug("[healthdcatap][parsed_creators] %r", creators)

        agents = self._parse_agents_with_contact_point(dataset_ref, HEALTHDCATAP.hdab)
        if agents:
            dataset_dict["hdab"] = agents
            log.debug("[healthdcatap][parsed_hdab] %r", agents)

        generated_values = self._parse_was_generated_by(dataset_ref)
        if generated_values:
            dataset_dict["was_generated_by"] = generated_values

        quality_annotations = self._parse_quality_annotation(dataset_ref)
        if quality_annotations:
            dataset_dict["quality_annotation"] = quality_annotations

        legal_basis_values = self._parse_legal_basis(dataset_ref)
        if legal_basis_values:
            dataset_dict["legal_basis"] = legal_basis_values

        purpose_values = self._parse_purpose(dataset_ref)
        if purpose_values:
            dataset_dict["purpose"] = purpose_values

        dataset_dict["retention_period"] = self._parse_retention_period(dataset_ref)

        for distribution_ref in self._distributions(dataset_ref):
            for resource_dict in dataset_dict.get("resources", []):
                if resource_dict.get("distribution_ref") == str(distribution_ref):
                    resource_dict["retention_period"] = self._parse_retention_period(
                        distribution_ref
                    )

    def __parse_healthdcat_intvalues(self, dataset_dict, dataset_ref):
        for key, predicate in (
            ("min_typical_age", HEALTHDCATAP.minTypicalAge),
            ("max_typical_age", HEALTHDCATAP.maxTypicalAge),
            ("number_of_records", HEALTHDCATAP.numberOfRecords),
            ("number_of_unique_individuals", HEALTHDCATAP.numberOfUniqueIndividuals),
        ):
            value = self._object_value_int(dataset_ref, predicate)
            if value is not None:
                dataset_dict[key] = value

    def __parse_healthdcat_stringvalues(self, dataset_dict, dataset_ref):
        for key, predicate in (
            ("analytics", HEALTHDCATAP.analytics),
            ("code_values", HEALTHDCATAP.hasCodeValues),
            ("coding_system", HEALTHDCATAP.hasCodingSystem),
            ("health_category", HEALTHDCATAP.healthCategory),
            ("health_theme", HEALTHDCATAP.healthTheme),
            ("personal_data", DPV.hasPersonalData),
            ("population_coverage", HEALTHDCATAP.populationCoverage),
            ("publisher_note", HEALTHDCATAP.publisherNote),
            ("publisher_type", HEALTHDCATAP.publisherType),
        ):
            values = self._object_value_list(dataset_ref, predicate)
            if values:
                dataset_dict[key] = values

    def __parse_healthdcat_booleanvalues(self, dataset_dict, dataset_ref):
        value = self._object_value(dataset_ref, HEALTHDCATAP.trustedDataHolder)
        if value is not None:
            lowered = value.lower()
            if lowered in ("true", "false"):
                dataset_dict["trusted_data_holder"] = lowered == "true"

    def _parse_spatial_values(self, dataset_ref):
        spatial_values = []

        for spatial_ref in self.g.objects(dataset_ref, DCT.spatial):
            value = None

            if isinstance(spatial_ref, URIRef):
                value = str(spatial_ref).strip()

            elif isinstance(spatial_ref, BNode):
                identifier = self._object_value(spatial_ref, DCT.identifier)
                if self._is_uri(identifier):
                    value = identifier

                if not value:
                    exact_match = self._object_value(spatial_ref, SKOS.exactMatch)
                    if self._is_uri(exact_match):
                        value = exact_match

                if not value:
                    same_as = self._object_value(spatial_ref, OWL.sameAs)
                    if self._is_uri(same_as):
                        value = same_as

            if self._is_uri(value) and value not in spatial_values:
                spatial_values.append(value)

            log.debug(
                "[healthdcatap][parse_spatial] dataset_ref=%s spatial_ref=%r parsed_value=%r",
                dataset_ref,
                spatial_ref,
                value,
            )

        log.debug("[healthdcatap][parsed_spatial] dataset_ref=%s spatial=%r", dataset_ref, spatial_values)
        return spatial_values

    def _parse_agents_with_contact_point(self, subject_ref, predicate):
        agents = []

        def _first_value(node, pred, strip_mailto=False):
            for obj in self.g.objects(node, pred):
                if isinstance(obj, (URIRef, Literal)):
                    value = str(obj).strip()
                else:
                    continue

                if strip_mailto and value.startswith("mailto:"):
                    value = value[len("mailto:"):].strip()

                if value:
                    return value
            return None

        def _set_if_missing(target, key, value):
            if value and not target.get(key):
                target[key] = value

        def _append_or_set(target, key, value):
            if not value:
                return

            current = target.get(key)
            if not current:
                target[key] = value
            elif current != value:
                log.debug(
                    "[healthdcatap][parse_agent:duplicate_value] predicate=%s key=%s current=%r new=%r",
                    predicate, key, current, value
                )

        for agent_ref in self.g.objects(subject_ref, predicate):
            if not isinstance(agent_ref, (URIRef, BNode)):
                continue

            agent = {}
            cp_count = 0
            oh_count = 0
            soh_count = 0

            name = _first_value(agent_ref, FOAF.name)
            _set_if_missing(agent, "name", name)

            agent_type = _first_value(agent_ref, DCT.type)
            _set_if_missing(agent, "type", agent_type)

            description = _first_value(agent_ref, DCT.description)
            _set_if_missing(agent, "description", description)

            homepage = _first_value(agent_ref, FOAF.homepage)
            _set_if_missing(agent, "url", homepage)

            mailbox = _first_value(agent_ref, FOAF.mbox, strip_mailto=True)
            _set_if_missing(agent, "email", mailbox)

            log.debug(
                "[healthdcatap][parse_agent:base] predicate=%s agent_ref=%s base=%r",
                predicate, agent_ref, agent
            )

            for cp_ref in self.g.objects(agent_ref, CV.contactPoint):
                if not isinstance(cp_ref, (URIRef, BNode)):
                    continue

                cp_count += 1

                cp_email = _first_value(cp_ref, CV.email, strip_mailto=True)
                _append_or_set(agent, "email", cp_email)

                contact_page = _first_value(cp_ref, CV.contactPage)
                _append_or_set(agent, "contact_page", contact_page)

                telephone = _first_value(cp_ref, CV.telephone)
                _append_or_set(agent, "telephone", telephone)

                log.debug(
                    "[healthdcatap][parse_contact_point] predicate=%s agent_ref=%s cp_ref=%s values=%r",
                    predicate,
                    agent_ref,
                    cp_ref,
                    {
                        "email": cp_email,
                        "contact_page": contact_page,
                        "telephone": telephone,
                    },
                )

                for oh_ref in self.g.objects(cp_ref, CV.openingHours):
                    if not isinstance(oh_ref, (URIRef, BNode)):
                        continue

                    oh_count += 1

                    opening_hours_description = _first_value(oh_ref, DCT.description)
                    _append_or_set(agent, "opening_hours_description", opening_hours_description)

                    opening_hours_frequency = _first_value(oh_ref, CV.frequency)
                    _append_or_set(agent, "opening_hours_frequency", opening_hours_frequency)

                    log.debug(
                        "[healthdcatap][parse_opening_hours] predicate=%s agent_ref=%s cp_ref=%s oh_ref=%s values=%r",
                        predicate,
                        agent_ref,
                        cp_ref,
                        oh_ref,
                        {
                            "opening_hours_description": opening_hours_description,
                            "opening_hours_frequency": opening_hours_frequency,
                        },
                    )

                for soh_ref in self.g.objects(cp_ref, CV.specialOpeningHoursSpecification):
                    if not isinstance(soh_ref, (URIRef, BNode)):
                        continue

                    soh_count += 1

                    special_opening_hours_description = _first_value(soh_ref, DCT.description)
                    _append_or_set(
                        agent,
                        "special_opening_hours_description",
                        special_opening_hours_description,
                    )

                    special_opening_hours_frequency = _first_value(soh_ref, CV.frequency)
                    _append_or_set(
                        agent,
                        "special_opening_hours_frequency",
                        special_opening_hours_frequency,
                    )

                    log.debug(
                        "[healthdcatap][parse_special_opening_hours] predicate=%s agent_ref=%s cp_ref=%s soh_ref=%s values=%r",
                        predicate,
                        agent_ref,
                        cp_ref,
                        soh_ref,
                        {
                            "special_opening_hours_description": special_opening_hours_description,
                            "special_opening_hours_frequency": special_opening_hours_frequency,
                        },
                    )

            if agent:
                log.debug(
                    "[healthdcatap][parse_agent:final] predicate=%s agent_ref=%s contact_points=%s opening_hours=%s special_opening_hours=%s parsed=%r",
                    predicate,
                    agent_ref,
                    cp_count,
                    oh_count,
                    soh_count,
                    agent,
                )
                agents.append(agent)
            else:
                log.debug(
                    "[healthdcatap][parse_agent:empty] predicate=%s agent_ref=%s",
                    predicate,
                    agent_ref,
                )

        log.debug("[healthdcatap][parsed_agents] predicate=%s agents=%r", predicate, agents)
        return agents



    def _parse_was_generated_by(self, dataset_ref):
        values = []
        for activity_ref in self.g.objects(dataset_ref, PROV.wasGeneratedBy):
            for activity_type in self.g.objects(activity_ref, DCT.type):
                if isinstance(activity_type, URIRef):
                    values.append(str(activity_type))
        return values

    def _parse_conforms_to_values(self, dataset_ref):
        conforms_to_values = []
        seen = set()

        for standard_ref in self.g.objects(dataset_ref, DCT.conformsTo):
            uri = None
            label = None

            if isinstance(standard_ref, URIRef):
                uri = str(standard_ref)
                label = self._object_value(standard_ref, RDFS.label)

            elif isinstance(standard_ref, BNode):
                about_uri = self._object_value(standard_ref, RDF.about)
                if self._is_uri(about_uri):
                    uri = about_uri
                else:
                    for candidate in self.g.objects(standard_ref, OWL.sameAs):
                        if isinstance(candidate, URIRef):
                            uri = str(candidate)
                            break
                    if not uri:
                        for candidate in self.g.objects(standard_ref, DCT.identifier):
                            candidate = str(candidate).strip()
                            if self._is_uri(candidate):
                                uri = candidate
                                break
                label = self._object_value(standard_ref, RDFS.label)

            if not self._is_uri(uri) or uri in seen:
                continue

            item = {"uri": uri}
            if label:
                item["label"] = label

            conforms_to_values.append(item)
            seen.add(uri)

        return conforms_to_values

    def _parse_documentation_values(self, dataset_ref):
        documentation_values = []
        seen = set()

        for doc_ref in self.g.objects(dataset_ref, FOAF.page):
            uri = None

            if isinstance(doc_ref, URIRef):
                uri = str(doc_ref).strip()
            elif isinstance(doc_ref, BNode):
                for candidate in self.g.objects(doc_ref, RDF.about):
                    candidate = str(candidate).strip()
                    if self._is_uri(candidate):
                        uri = candidate
                        break
                if not uri:
                    for candidate in self.g.objects(doc_ref, OWL.sameAs):
                        if isinstance(candidate, URIRef):
                            uri = str(candidate).strip()
                            break
                if not uri:
                    for candidate in self.g.objects(doc_ref, DCT.identifier):
                        candidate = str(candidate).strip()
                        if self._is_uri(candidate):
                            uri = candidate
                            break

            if not self._is_uri(uri) or uri in seen:
                continue

            documentation_values.append({"uri": uri})
            seen.add(uri)

        return documentation_values

    def _parse_landing_page_values(self, dataset_ref):
        landing_page_values = []
        seen = set()

        for page_ref in self.g.objects(dataset_ref, DCAT.landingPage):
            uri = None

            if isinstance(page_ref, URIRef):
                uri = str(page_ref).strip()
            elif isinstance(page_ref, BNode):
                for candidate in self.g.objects(page_ref, RDF.about):
                    candidate = str(candidate).strip()
                    if self._is_uri(candidate):
                        uri = candidate
                        break
                if not uri:
                    for candidate in self.g.objects(page_ref, OWL.sameAs):
                        if isinstance(candidate, URIRef):
                            uri = str(candidate).strip()
                            break
                if not uri:
                    for candidate in self.g.objects(page_ref, DCT.identifier):
                        candidate = str(candidate).strip()
                        if self._is_uri(candidate):
                            uri = candidate
                            break

            if not self._is_uri(uri) or uri in seen:
                continue

            landing_page_values.append(uri)
            seen.add(uri)

        return landing_page_values

    def _parse_quality_annotation(self, dataset_ref):
        quality_annotation = []
        for annotation_ref in self.g.objects(dataset_ref, DQV.hasQualityAnnotation):
            annotation_dict = {}
            body = self._object_value(annotation_ref, OA.hasBody)
            if body and isinstance(body, str) and body.startswith(("http://", "https://")):
                annotation_dict["body"] = body
            target = self._object_value(annotation_ref, OA.hasTarget)
            if target and isinstance(target, str) and target.startswith(("http://", "https://")):
                annotation_dict["target"] = target
            motivation = self._object_value(annotation_ref, OA.motivatedBy)
            if motivation:
                annotation_dict["motivated_by"] = motivation
            if annotation_dict:
                quality_annotation.append(annotation_dict)
        return quality_annotation

    def _parse_legal_basis(self, dataset_ref):
        legal_basis_values = []

        for legal_basis_ref in self.g.objects(dataset_ref, DPV.hasLegalBasis):
            item = {}

            description = self._object_value(legal_basis_ref, DCT.description)
            if description:
                item["description"] = description

            source = self._object_value(legal_basis_ref, DCT.source)
            if source:
                item["source"] = source

            if item:
                legal_basis_values.append(item)

        return legal_basis_values

    def _parse_purpose(self, dataset_ref):
        purpose_values = []

        for purpose_ref in self.g.objects(dataset_ref, DPV.hasPurpose):
            if isinstance(purpose_ref, URIRef):
                purpose_values.append(str(purpose_ref))
                continue

            label = self._object_value(purpose_ref, RDFS.label)
            if label:
                purpose_values.append(label)
                continue

            description = self._object_value(purpose_ref, DCT.description)
            if description:
                purpose_values.append(description)

        return purpose_values

    def _parse_retention_period(self, subject_ref):
        retention_start, retention_end = self._time_interval(
            subject_ref, HEALTHDCATAP.retentionPeriod, dcat_ap_version=2
        )
        retention_dict = {}
        if retention_start is not None:
            retention_dict["start"] = retention_start
        if retention_end is not None:
            retention_dict["end"] = retention_end
        return [retention_dict] if retention_dict else []

    def _parse_qualified_attributions(self, dataset_ref):
        qualified_attributions = []

        for attribution_ref in self.g.objects(dataset_ref, PROV.qualifiedAttribution):
            item = {}

            role = self._object_value(attribution_ref, DCAT.hadRole)
            if role:
                item["qualified_attribution_role"] = role

            agent_ref = None
            for obj in self.g.objects(attribution_ref, PROV.agent):
                agent_ref = obj
                break

            if agent_ref is not None:
                agent_name = self._object_value(agent_ref, FOAF.name)
                agent_homepage = self._object_value(agent_ref, FOAF.homepage)
                agent_email = self._object_value(agent_ref, FOAF.mbox)
                agent_type = self._object_value(agent_ref, DCT.type)

                if agent_name:
                    item["qualified_attribution_agent_name"] = agent_name
                if agent_homepage:
                    item["qualified_attribution_agent_contact_page"] = agent_homepage
                if agent_email:
                    item["qualified_attribution_agent_email"] = str(agent_email).replace("mailto:", "")
                if agent_type:
                    item["qualified_attribution_agent_type"] = agent_type

            if item:
                qualified_attributions.append(item)

        return qualified_attributions


    def _normalize_text(self, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def _normalize_uri_value(self, value):
        value = self._normalize_text(value)
        return value if self._is_uri(value) else None

    def _bind_namespaces(self):
        for prefix, namespace in {
            "healthdcatap": HEALTHDCATAP,
            "dpv": DPV,
            "pd": PD,
            "dqv": DQV,
            "oa": OA,
            "vcard": VCARD,
            "cv": CV,
            "skos": SKOS,
            "dcatap": DCATAP,
            "eli": ELI,
            "prov": PROV,
            "time": TIME,
        }.items():
            self.g.bind(prefix, namespace)

    def _is_uri(self, value):
        return isinstance(value, str) and value.startswith(("http://", "https://"))

    def _normalize_uri_list(self, values):
        if not values:
            return []
        if not isinstance(values, list):
            values = [values]

        normalized = []
        for value in values:
            if isinstance(value, dict):
                uri = value.get("uri")
                if self._is_uri(uri):
                    normalized.append(uri)
            elif self._is_uri(value):
                normalized.append(value)
        return normalized

    def _normalize_uri_dict_list(self, values):
        if not values:
            return []
        if not isinstance(values, list):
            values = [values]

        normalized = []
        seen = set()

        for value in values:
            uri = None

            if isinstance(value, dict):
                uri = value.get("uri")
            elif self._is_uri(value):
                uri = value

            if uri and uri not in seen:
                normalized.append({"uri": uri})
                seen.add(uri)

        return normalized



    def _coerce_to_list(self, values):
        if values in (None, ""):
            return []

        if isinstance(values, list):
            return values

        if isinstance(values, tuple):
            return list(values)

        if isinstance(values, str):
            stripped = values.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                inner = stripped[1:-1].strip()
                if not inner:
                    return []
                parts = [part.strip() for part in inner.split(",")]
                cleaned = []
                for part in parts:
                    part = part.strip().strip('"').strip("'")
                    if part:
                        cleaned.append(part)
                return cleaned
            return [values]

        return [values]

    def _parse_uri_values(self, dataset_ref, predicate):
        values = []
        seen = set()

        for obj in self.g.objects(dataset_ref, predicate):
            uri = None

            if isinstance(obj, URIRef):
                uri = str(obj).strip()
            elif isinstance(obj, BNode):
                for candidate in self.g.objects(obj, OWL.sameAs):
                    if isinstance(candidate, URIRef):
                        uri = str(candidate).strip()
                        break
                if not uri:
                    for candidate in self.g.objects(obj, DCT.identifier):
                        candidate = str(candidate).strip()
                        if self._is_uri(candidate):
                            uri = candidate
                            break

            if self._is_uri(uri) and uri not in seen:
                values.append(uri)
                seen.add(uri)

        return values

    def _normalize_multi_uri_choice_field(self, dataset_dict, dataset_ref, field_name, predicate):
        current_values = self._coerce_to_list(dataset_dict.get(field_name))
        normalized = []
        seen = set()

        for value in current_values:
            uri = None

            if isinstance(value, dict):
                uri = value.get("uri") or value.get("value") or value.get("identifier")
            elif self._is_uri(value):
                uri = value

            if self._is_uri(uri):
                uri = str(uri).strip()
                if uri not in seen:
                    normalized.append(uri)
                    seen.add(uri)

        if not normalized and dataset_ref is not None:
            for uri in self._parse_uri_values(dataset_ref, predicate):
                if uri not in seen:
                    normalized.append(uri)
                    seen.add(uri)

        if normalized:
            dataset_dict[field_name] = normalized

    def _normalize_applicable_legislation_fields(self, dataset_dict):
        dataset_legislation = dataset_dict.get("applicable_legislation")
        if dataset_legislation:
            dataset_dict["applicable_legislation"] = self._normalize_uri_dict_list(
                dataset_legislation
            )

        for resource_dict in dataset_dict.get("resources", []):
            if not isinstance(resource_dict, dict):
                continue

            resource_legislation = resource_dict.get("applicable_legislation")
            if resource_legislation:
                resource_dict["applicable_legislation"] = self._normalize_uri_dict_list(
                    resource_legislation
                )

    def _normalize_conforms_to_field(self, dataset_dict, dataset_ref):
        parsed_values = self._parse_conforms_to_values(dataset_ref)
        existing_values = dataset_dict.get("conforms_to")

        if existing_values and not isinstance(existing_values, list):
            existing_values = [existing_values]
        elif not existing_values:
            existing_values = []

        normalized = []
        seen = set()

        for value in list(parsed_values) + list(existing_values):
            uri = None
            label = None

            if isinstance(value, dict):
                uri = value.get("uri") or value.get("value") or value.get("identifier")
                label = value.get("label") or value.get("title") or value.get("text")
            elif self._is_uri(value):
                uri = value

            if not self._is_uri(uri) or uri in seen:
                continue

            item = {"uri": uri}
            if label:
                item["label"] = str(label).strip()

            normalized.append(item)
            seen.add(uri)

        dataset_dict["conforms_to"] = normalized


    def _normalize_coding_system_field(self, dataset_dict, dataset_ref):
        existing_values = dataset_dict.get("coding_system")

        if existing_values and not isinstance(existing_values, list):
            existing_values = [existing_values]
        elif not existing_values:
            existing_values = []

        normalized = []
        seen = set()

        for value in existing_values:
            uri = None
            label = None

            if isinstance(value, dict):
                uri = value.get("uri") or value.get("value") or value.get("identifier")
                label = value.get("label") or value.get("title") or value.get("text")
            elif self._is_uri(value):
                uri = value

            if not self._is_uri(uri):
                continue

            uri = str(uri).strip()
            if uri in seen:
                continue

            item = {"uri": uri}
            if label:
                item["label"] = str(label).strip()

            normalized.append(item)
            seen.add(uri)

        if normalized:
            dataset_dict["coding_system"] = normalized

    def _normalize_documentation_field(self, dataset_dict, dataset_ref):
        parsed_values = self._parse_documentation_values(dataset_ref)
        existing_values = dataset_dict.get("documentation")

        if existing_values and not isinstance(existing_values, list):
            existing_values = [existing_values]
        elif not existing_values:
            existing_values = []

        normalized = []
        seen = set()

        for value in list(parsed_values) + list(existing_values):
            uri = None

            if isinstance(value, dict):
                uri = value.get("uri") or value.get("value") or value.get("identifier")
            elif self._is_uri(value):
                uri = value

            if not self._is_uri(uri):
                continue

            uri = str(uri).strip()
            if uri in seen:
                continue

            normalized.append({"uri": uri})
            seen.add(uri)

        dataset_dict["documentation"] = normalized

    def _normalize_landing_page_field(self, dataset_dict, dataset_ref):
        parsed_values = self._parse_landing_page_values(dataset_ref)
        existing_values = self._coerce_to_list(dataset_dict.get("landing_page"))

        normalized = []
        seen = set()

        for value in list(parsed_values) + list(existing_values):
            uri = None

            if isinstance(value, dict):
                uri = value.get("uri") or value.get("value") or value.get("identifier")
            elif self._is_uri(value):
                uri = value

            if not self._is_uri(uri):
                continue

            uri = str(uri).strip()
            if uri in seen:
                continue

            normalized.append(uri)
            seen.add(uri)

        dataset_dict["landing_page"] = normalized


    def _remove_predicate_objects(self, subject_ref, predicate):
        for obj in list(self.g.objects(subject_ref, predicate)):
            self.g.remove((subject_ref, predicate, obj))
            if isinstance(obj, BNode):
                self._remove_bnode_tree(obj)

    def _remove_bnode_tree(self, root):
        for _, p, o in list(self.g.triples((root, None, None))):
            self.g.remove((root, p, o))
            if isinstance(o, BNode):
                self._remove_bnode_tree(o)

    def _remove_uri_agent_artifacts(self, agent_ref):
        for p, o in list(self.g.predicate_objects(agent_ref)):
            if p == CV.contactPoint and isinstance(o, BNode):
                self._remove_bnode_tree(o)
            self.g.remove((agent_ref, p, o))

    def _get_scheme_rule(self, uri):
        uri = str(uri)
        for rule in CONCEPT_SCHEME_RULES:
            if uri.startswith(rule["prefix"]):
                return rule
        return None

    def _code_from_uri(self, uri):
        return unquote(str(uri).rstrip("/").split("/")[-1])

    def _humanize_code(self, code):
        if not code:
            return None
        text = str(code).replace("_", " ").replace("-", " ").strip()
        if text.isupper() and len(text) <= 5:
            return text
        return text.title()

    def _label_for_uri(self, uri, explicit_label=None):
        if isinstance(explicit_label, dict):
            explicit_label = explicit_label.get("en") or explicit_label.get("es") or next(
                (v for v in explicit_label.values() if v), None
            )
        if explicit_label:
            return explicit_label

        rule = self._get_scheme_rule(uri)
        code = self._code_from_uri(uri)
        if rule:
            label = rule.get("labels", {}).get(code)
            if label:
                return label

        if str(uri).startswith("https://www.iana.org/assignments/media-types/"):
            return code

        return self._humanize_code(code)

    def _literal_for_label(self, label):
        return Literal(label, lang="en") if label else None

    def _enrich_concept(self, uri_ref, predicate=None, label=None, extra_type=None):
        uri_ref = URIRef(str(uri_ref))
        self.g.add((uri_ref, RDF.type, SKOS.Concept))

        rule = self._get_scheme_rule(uri_ref)
        if extra_type is not None:
            self.g.add((uri_ref, RDF.type, extra_type))
        elif rule and rule.get("class") is not None:
            self.g.add((uri_ref, RDF.type, rule["class"]))

        scheme = None
        if rule:
            scheme = rule.get("scheme")
        elif predicate == DCT.language:
            scheme = URIRef("http://publications.europa.eu/resource/authority/language")
        elif predicate == DCT.accessRights:
            scheme = URIRef("http://publications.europa.eu/resource/authority/access-right")
        elif predicate == DCT.accrualPeriodicity:
            scheme = URIRef("http://publications.europa.eu/resource/authority/frequency")
        elif predicate == DCT.type:
            scheme = URIRef("http://publications.europa.eu/resource/authority/dataset-type")
        elif predicate == DCAT.theme:
            scheme = URIRef("http://publications.europa.eu/resource/authority/data-theme")
        elif predicate == HEALTHDCATAP.healthTheme:
            scheme = URIRef("http://13.81.34.152:1101/resource/authority/health-theme")
        elif predicate == HEALTHDCATAP.publisherType:
            scheme = URIRef("http://13.81.34.152:1101/resource/authority/publisher-type")
        elif predicate == PROV.wasGeneratedBy:
            scheme = URIRef("http://13.81.34.152:1101/resource/authority/health-activity")

        if scheme is not None:
            self.g.remove((uri_ref, SKOS.inScheme, None))
            self.g.add((uri_ref, SKOS.inScheme, scheme))
            

        self.g.remove((uri_ref, SKOS.prefLabel, None))
        self.g.remove((uri_ref, RDFS.label, None))
        concept_label = self._label_for_uri(uri_ref, label)
        literal = self._literal_for_label(concept_label)
        if literal is not None:
            self.g.add((uri_ref, SKOS.prefLabel, literal))

    def _add_list_values(self, dataset_dict, dataset_ref, key, predicate, as_uri=False, concept=False):
        values = self._get_dict_value(dataset_dict, key)
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        for value in values:
            if isinstance(value, dict):
                uri = value.get("uri")
                label = value.get("label") or value.get("title") or value.get("text")
                if as_uri:
                    if not self._is_uri(uri):
                        continue
                    uri_ref = URIRef(uri)
                    self.g.add((dataset_ref, predicate, uri_ref))
                    if concept:
                        self._enrich_concept(uri_ref, predicate=predicate, label=label)
                elif label:
                    self.g.add((dataset_ref, predicate, Literal(label)))
                continue

            if as_uri:
                if not self._is_uri(value):
                    continue
                uri_ref = URIRef(value)
                self.g.add((dataset_ref, predicate, uri_ref))
                if concept:
                    self._enrich_concept(uri_ref, predicate=predicate)
            else:
                self.g.add((dataset_ref, predicate, Literal(value)))

    def _add_conforms_to_values(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "conforms_to")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        self._remove_predicate_objects(dataset_ref, DCT.conformsTo)

        for value in values:
            if isinstance(value, dict):
                uri = value.get("uri")
                label = value.get("label")
            else:
                uri = value
                label = None

            if not self._is_uri(uri):
                continue

            uri_ref = URIRef(uri)

            self.g.add((dataset_ref, DCT.conformsTo, uri_ref))
            self.g.add((uri_ref, RDF.type, DCT.Standard))

            if label:
                self.g.remove((uri_ref, RDFS.label, None))
                self.g.add((uri_ref, RDFS.label, Literal(label)))


    def _add_coding_system_values(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "coding_system")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        self._remove_predicate_objects(dataset_ref, HEALTHDCATAP.hasCodingSystem)

        seen = set()

        for value in values:
            uri = None
            label = None

            if isinstance(value, dict):
                uri = value.get("uri") or value.get("value") or value.get("identifier")
                label = value.get("label") or value.get("title") or value.get("text")
            else:
                uri = value

            if not self._is_uri(uri):
                continue

            uri = str(uri).strip()
            if uri in seen:
                continue
            seen.add(uri)

            uri_ref = URIRef(uri)
            self.g.add((dataset_ref, HEALTHDCATAP.hasCodingSystem, uri_ref))
            self.g.add((uri_ref, RDF.type, DCT.Standard))

            if label:
                self.g.remove((uri_ref, RDFS.label, None))
                self.g.add((uri_ref, RDFS.label, Literal(str(label).strip())))


    def _add_documentation_values(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "documentation")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        self._remove_predicate_objects(dataset_ref, FOAF.page)

        for value in values:
            if isinstance(value, dict):
                uri = value.get("uri")
            else:
                uri = value

            if not self._is_uri(uri):
                continue

            uri_ref = URIRef(uri)
            self.g.add((dataset_ref, FOAF.page, uri_ref))
            self.g.add((uri_ref, RDF.type, FOAF.Document))

    def _add_landing_page_values(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "landing_page")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        self._remove_predicate_objects(dataset_ref, DCAT.landingPage)

        for value in values:
            if isinstance(value, dict):
                uri = value.get("uri")
            else:
                uri = value

            if not self._is_uri(uri):
                continue

            uri_ref = URIRef(uri)
            self.g.add((dataset_ref, DCAT.landingPage, uri_ref))
            self.g.add((uri_ref, RDF.type, FOAF.Document))

    def _add_health_category_values(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "health_category")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        scheme = URIRef("http://13.81.34.152:1101/resource/authority/healthcategories")

        self._remove_predicate_objects(dataset_ref, HEALTHDCATAP.healthCategory)

        for value in values:
            if isinstance(value, dict):
                uri = value.get("uri")
            else:
                uri = value

            if not self._is_uri(uri):
                continue

            uri_ref = URIRef(uri)
            code = self._code_from_uri(uri_ref)

            self.g.add((dataset_ref, HEALTHDCATAP.healthCategory, uri_ref))

            self.g.remove((uri_ref, RDF.type, None))
            self.g.remove((uri_ref, HEALTHDCATAP.hasCodingSystem, None))
            self.g.remove((uri_ref, SKOS.inScheme, None))
            self.g.remove((uri_ref, SKOS.prefLabel, None))
            self.g.remove((uri_ref, RDFS.label, None))

            self.g.add((uri_ref, RDF.type, SKOS.Concept))
            self.g.add((uri_ref, HEALTHDCATAP.hasCodingSystem, scheme))
            self.g.add((uri_ref, SKOS.inScheme, scheme))
            self.g.add((uri_ref, SKOS.prefLabel, Literal(code, lang="en")))


    def _add_was_generated_by(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "was_generated_by")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        self._remove_predicate_objects(dataset_ref, PROV.wasGeneratedBy)

        for value in values:
            if isinstance(value, dict):
                uri = value.get("uri")
                label = value.get("label") or value.get("title") or value.get("text")
            else:
                uri = value
                label = None

            if not self._is_uri(uri):
                continue

            activity_ref = BNode()
            type_ref = URIRef(uri)

            self.g.add((dataset_ref, PROV.wasGeneratedBy, activity_ref))
            self.g.add((activity_ref, RDF.type, PROV.Activity))
            self.g.add((activity_ref, DCT.type, type_ref))

            self._enrich_concept(type_ref, predicate=PROV.wasGeneratedBy, label=label)

    def _add_legal_basis(self, dataset_ref, legal_basis_values):
        if not legal_basis_values:
            return

        if not isinstance(legal_basis_values, list):
            legal_basis_values = [legal_basis_values]

        self._remove_predicate_objects(dataset_ref, DPV.hasLegalBasis)
        self._remove_predicate_objects(dataset_ref, DCT.relation)
        self._remove_predicate_objects(dataset_ref, PROV.qualifiedAttribution)

        for item in legal_basis_values:
            if not isinstance(item, dict):
                continue

            description = item.get("description")
            source = item.get("source")

            if not description and not source:
                continue

            legal_basis_ref = BNode()
            self.g.add((dataset_ref, DPV.hasLegalBasis, legal_basis_ref))
            self.g.add((legal_basis_ref, RDF.type, DPV.LegalBasis))

            if description:
                self.g.add((legal_basis_ref, DCT.description, Literal(description, lang="en")))

            if source:
                if self._is_uri(source):
                    self.g.add((legal_basis_ref, DCT.source, URIRef(source)))
                else:
                    self.g.add((legal_basis_ref, DCT.source, Literal(source)))

    def _add_purpose_values(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "purpose")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        self._remove_predicate_objects(dataset_ref, DPV.hasPurpose)

        for value in values:
            if not value:
                continue

            if isinstance(value, dict):
                label = value.get("label") or value.get("text") or value.get("description")
                uri = value.get("uri")
                if self._is_uri(uri):
                    purpose_ref = URIRef(uri)
                    self.g.add((dataset_ref, DPV.hasPurpose, purpose_ref))
                    self.g.add((purpose_ref, RDF.type, DPV.Purpose))
                    if label:
                        self.g.remove((purpose_ref, RDFS.label, None))
                        self.g.add((purpose_ref, RDFS.label, Literal(label)))
                    continue
                value = label

            if self._is_uri(value):
                purpose_ref = URIRef(value)
                self.g.add((dataset_ref, DPV.hasPurpose, purpose_ref))
                self.g.add((purpose_ref, RDF.type, DPV.Purpose))
            else:
                purpose_ref = BNode()
                self.g.add((dataset_ref, DPV.hasPurpose, purpose_ref))
                self.g.add((purpose_ref, RDF.type, DPV.Purpose))
                self.g.add((purpose_ref, RDFS.label, Literal(value)))

    def _fix_dataset_concepts(self, dataset_dict, dataset_ref):
        for field_name, predicate, concept in (
            ("theme", DCAT.theme, True),
            ("language", DCT.language, True),
            ("access_rights", DCT.accessRights, True),
            ("frequency", DCT.accrualPeriodicity, True),
            ("dcat_type", DCT.type, True),
            ("applicable_legislation", DCATAP.applicableLegislation, False),
        ):
            self._remove_predicate_objects(dataset_ref, predicate)
            self._add_list_values(
                dataset_dict,
                dataset_ref,
                field_name,
                predicate,
                as_uri=True,
                concept=concept,
            )

    def _fix_distribution_concepts(self, resource_dict, distribution_ref):
        for predicate, explicit_type in (
            (DCT.format, DCT.MediaTypeOrExtent),
            (DCAT.mediaType, DCT.MediaType),
        ):
            values = list(self.g.objects(distribution_ref, predicate))
            for obj in values:
                if isinstance(obj, URIRef):
                    self._enrich_concept(obj, predicate=predicate, extra_type=explicit_type)

    def _fix_spatial(self, dataset_dict, dataset_ref):
        self._remove_predicate_objects(dataset_ref, DCT.spatial)

        spatial_values = self._get_dict_value(dataset_dict, "spatial") or []
        if not isinstance(spatial_values, list):
            spatial_values = [spatial_values]

        for spatial in spatial_values:
            if isinstance(spatial, dict):
                uri = spatial.get("uri")
                label = spatial.get("text") or spatial.get("label")
                if self._is_uri(uri):
                    uri_ref = URIRef(uri)
                    self.g.add((dataset_ref, DCT.spatial, uri_ref))
                    self.g.add((uri_ref, RDF.type, DCT.Location))
                    if label:
                        self.g.remove((uri_ref, SKOS.prefLabel, None))
                        self.g.add((uri_ref, SKOS.prefLabel, self._literal_for_label(label)))
            elif self._is_uri(spatial):
                uri_ref = URIRef(spatial)
                self.g.add((dataset_ref, DCT.spatial, uri_ref))
                self.g.add((uri_ref, RDF.type, DCT.Location))

    def _add_health_dataset_fields(self, dataset_dict, dataset_ref):
        self._add_list_values(dataset_dict, dataset_ref, "analytics", HEALTHDCATAP.analytics, as_uri=True)
        for value in self._get_dict_value(dataset_dict, "analytics") or []:
            uri = value.get("uri") if isinstance(value, dict) else value
            if self._is_uri(uri):
                self.g.add((URIRef(uri), RDF.type, DCAT.Distribution))

        self._add_list_values(dataset_dict, dataset_ref, "code_values", HEALTHDCATAP.hasCodeValues)
        self._add_coding_system_values(dataset_dict, dataset_ref)
        self._add_health_category_values(dataset_dict, dataset_ref)
        self._add_list_values(dataset_dict, dataset_ref, "health_theme", HEALTHDCATAP.healthTheme, as_uri=True, concept=True)
        self._add_was_generated_by(dataset_dict, dataset_ref)
        self._add_legal_basis(dataset_ref, self._get_dict_value(dataset_dict, "legal_basis"))
        self._add_list_values(dataset_dict, dataset_ref, "population_coverage", HEALTHDCATAP.populationCoverage)

        personal_data_values = self._get_dict_value(dataset_dict, "personal_data") or []
        if not isinstance(personal_data_values, list):
            personal_data_values = [personal_data_values]

        for value in personal_data_values:
            if isinstance(value, dict):
                uri = value.get("uri")
            else:
                uri = value

            if not self._is_uri(uri):
                continue

            uri_ref = URIRef(uri)
            self.g.add((dataset_ref, DPV.hasPersonalData, uri_ref))
            self.g.add((uri_ref, RDF.type, DPV.PersonalData))

        self._add_list_values(dataset_dict, dataset_ref, "publisher_note", HEALTHDCATAP.publisherNote)
        self._add_list_values(dataset_dict, dataset_ref, "publisher_type", HEALTHDCATAP.publisherType, as_uri=True, concept=True)
        self._add_purpose_values(dataset_dict, dataset_ref)
        self._add_temporal_resolution(dataset_dict, dataset_ref)

        trusted = self._get_dict_value(dataset_dict, "trusted_data_holder")
        if trusted not in (None, ""):
            if isinstance(trusted, str):
                trusted = trusted.lower() == "true"
            self.g.add((dataset_ref, HEALTHDCATAP.trustedDataHolder, Literal(bool(trusted), datatype=XSD.boolean)))

        for key, predicate in (
            ("min_typical_age", HEALTHDCATAP.minTypicalAge),
            ("max_typical_age", HEALTHDCATAP.maxTypicalAge),
            ("number_of_records", HEALTHDCATAP.numberOfRecords),
            ("number_of_unique_individuals", HEALTHDCATAP.numberOfUniqueIndividuals),
        ):
            self._add_nonneg_integer_triple(dataset_dict, dataset_ref, key, predicate)

        for concept_predicate in (
            DCAT.theme,
            DCT.type,
            DCT.accessRights,
            DCT.language,
            DCT.accrualPeriodicity,
            HEALTHDCATAP.healthTheme,
            HEALTHDCATAP.publisherType,
        ):
            for obj in self.g.objects(dataset_ref, concept_predicate):
                if isinstance(obj, URIRef):
                    self._enrich_concept(obj, predicate=concept_predicate)

    def _add_temporal_resolution(self, dataset_dict, dataset_ref):
        value = self._get_dict_value(dataset_dict, "temporal_resolution")
        if value in (None, ""):
            return

        self._remove_predicate_objects(dataset_ref, DCAT.temporalResolution)

        if isinstance(value, list):
            value = value[0] if value else None

        if value in (None, ""):
            return

        value = str(value).strip()
        self.g.add((dataset_ref, DCAT.temporalResolution, Literal(value, datatype=XSD.duration)))


    def _add_related_resource_values(self, dataset_dict, dataset_ref):
        values = self._get_dict_value(dataset_dict, "related_resource")
        if not values:
            return

        if not isinstance(values, list):
            values = [values]

        self._remove_predicate_objects(dataset_ref, DCT.relation)

        for value in values:
            uri = None
            label = None

            if isinstance(value, dict):
                uri = value.get("uri")
                label = value.get("label") or value.get("text")
            else:
                uri = value

            if not self._is_uri(uri):
                continue

            related_ref = URIRef(uri)
            self.g.add((dataset_ref, DCT.relation, related_ref))

            if label:
                self.g.remove((related_ref, RDFS.label, None))
                self.g.add((related_ref, RDFS.label, Literal(label)))

    def _add_qualified_attributions(self, dataset_ref, attributions):
        if not attributions:
            return

        if not isinstance(attributions, list):
            attributions = [attributions]

        self._remove_predicate_objects(dataset_ref, PROV.qualifiedAttribution)

        for item in attributions:
            if not isinstance(item, dict):
                continue

            role = item.get("qualified_attribution_role")
            agent_name = item.get("qualified_attribution_agent_name")
            agent_homepage = item.get("qualified_attribution_agent_contact_page")
            agent_email = item.get("qualified_attribution_agent_email")
            agent_type = item.get("qualified_attribution_agent_type")

            if not role or not agent_name:
                continue

            attribution_ref = BNode()
            agent_ref = BNode()

            self.g.add((dataset_ref, PROV.qualifiedAttribution, attribution_ref))
            self.g.add((attribution_ref, RDF.type, PROV.Attribution))

            if self._is_uri(role):
                self.g.add((attribution_ref, DCAT.hadRole, URIRef(role)))

            self.g.add((attribution_ref, PROV.agent, agent_ref))
            self.g.add((agent_ref, RDF.type, FOAF.Agent))
            self.g.add((agent_ref, RDF.type, FOAF.Organization))
            self.g.add((agent_ref, FOAF.name, Literal(agent_name)))

            if self._is_uri(agent_type):
                type_ref = URIRef(agent_type)
                self.g.add((agent_ref, DCT.type, type_ref))
                self._enrich_concept(type_ref, predicate=HEALTHDCATAP.publisherType)

            if self._is_uri(agent_homepage):
                self.g.add((agent_ref, FOAF.homepage, URIRef(agent_homepage)))

            if agent_email:
                email = agent_email
                if isinstance(email, str) and not email.startswith("mailto:"):
                    email = f"mailto:{email}"
                self.g.add((agent_ref, FOAF.mbox, URIRef(email)))

    def _add_health_agents(self, dataset_ref, dataset_dict):
        self._add_agent_with_contact_point(dataset_ref, DCT.publisher, dataset_dict.get("publisher"))
        self._add_agent_with_contact_point(dataset_ref, DCT.creator, dataset_dict.get("creator"))
        self._add_agent_with_contact_point(dataset_ref, HEALTHDCATAP.hdab, dataset_dict.get("hdab"))
        
    def _add_dataset_contact_points(self, dataset_ref, contacts):
        if not contacts:
            return

        if not isinstance(contacts, list):
            contacts = [contacts]

        self._remove_predicate_objects(dataset_ref, DCAT.contactPoint)

        for contact in contacts:
            if not isinstance(contact, dict):
                continue

            email = contact.get("email")
            url = contact.get("url")

            if not (email or url):
                continue

            cp_ref = BNode()

            self.g.add((dataset_ref, DCAT.contactPoint, cp_ref))
            self.g.add((cp_ref, RDF.type, VCARD.Kind))

            if email:
                if isinstance(email, str) and not email.startswith("mailto:"):
                    email = f"mailto:{email}"
                self.g.add((cp_ref, VCARD.hasEmail, URIRef(email)))

            if self._is_uri(url):
                self.g.add((cp_ref, VCARD.hasURL, URIRef(url)))     


    def _add_agent_with_contact_point(self, subject_ref, predicate, agents):
        if not agents:
            log.debug("[healthdcatap][serialize_agents:skip] predicate=%s reason=no_agents", predicate)
            return
        if not isinstance(agents, list):
            agents = [agents]

        self._remove_predicate_objects(subject_ref, predicate)

        for agent in agents:
            if not isinstance(agent, dict):
                log.debug("[healthdcatap][serialize_agent:skip] predicate=%s reason=not_dict agent=%r", predicate, agent)
                continue

            relevant_keys = (
                "name", "email", "url", "type", "description", "contact_page",
                "telephone", "opening_hours_description", "opening_hours_frequency",
                "special_opening_hours_description", "special_opening_hours_frequency",
            )
            if not any(self._normalize_text(agent.get(k)) for k in relevant_keys):
                log.debug("[healthdcatap][serialize_agent:skip] predicate=%s empty_agent=%r", predicate, agent)
                continue

            agent_uri = self._normalize_uri_value(agent.get("uri"))
            if predicate in (DCT.publisher, DCT.creator, HEALTHDCATAP.hdab):
                agent_ref = URIRef(agent_uri) if agent_uri else BNode()
            else:
                agent_ref = URIRef(agent_uri) if agent_uri else BNode()

            if isinstance(agent_ref, URIRef):
                self._remove_uri_agent_artifacts(agent_ref)

            self.g.add((subject_ref, predicate, agent_ref))
            self.g.add((agent_ref, RDF.type, FOAF.Agent))
            if predicate == DCT.creator:
                self.g.add((agent_ref, RDF.type, FOAF.Organization))

            name = self._normalize_text(agent.get("name"))
            if name:
                self.g.add((agent_ref, FOAF.name, Literal(name)))

            type_uri = self._normalize_uri_value(agent.get("type"))
            if type_uri:
                type_ref = URIRef(type_uri)
                self.g.add((agent_ref, DCT.type, type_ref))
                self._enrich_concept(type_ref, predicate=HEALTHDCATAP.publisherType)

            homepage = self._normalize_uri_value(agent.get("url"))
            if homepage:
                self.g.add((agent_ref, FOAF.homepage, URIRef(homepage)))

            email = self._normalize_text(agent.get("email"))
            if email:
                mbox = email if email.startswith("mailto:") else f"mailto:{email}"
                self.g.add((agent_ref, FOAF.mbox, URIRef(mbox)))

            description = self._normalize_text(agent.get("description"))
            if description:
                self.g.add((agent_ref, DCT.description, Literal(description)))

            contact_page = self._normalize_uri_value(agent.get("contact_page"))
            telephone = self._normalize_text(agent.get("telephone"))
            opening_hours_description = self._normalize_text(agent.get("opening_hours_description"))
            opening_hours_frequency = self._normalize_uri_value(agent.get("opening_hours_frequency"))
            special_opening_hours_description = self._normalize_text(agent.get("special_opening_hours_description"))
            special_opening_hours_frequency = self._normalize_uri_value(agent.get("special_opening_hours_frequency"))

            cp_payload = {
                "email": email,
                "contact_page": contact_page,
                "telephone": telephone,
                "opening_hours_description": opening_hours_description,
                "opening_hours_frequency": opening_hours_frequency,
                "special_opening_hours_description": special_opening_hours_description,
                "special_opening_hours_frequency": special_opening_hours_frequency,
            }

            if any(cp_payload.values()):
                cp = BNode()
                self.g.add((agent_ref, CV.contactPoint, cp))
                self.g.add((cp, RDF.type, CV.ContactPoint))

                if email:
                    self.g.add((cp, CV.email, Literal(email)))
                if contact_page:
                    page_ref = URIRef(contact_page)
                    self.g.add((cp, CV.contactPage, page_ref))
                    self.g.add((page_ref, RDF.type, FOAF.Document))
                if telephone:
                    self.g.add((cp, CV.telephone, Literal(telephone)))

                if opening_hours_description or opening_hours_frequency:
                    oh_ref = BNode()
                    self.g.add((cp, CV.openingHours, oh_ref))
                    self.g.add((oh_ref, RDF.type, TIME.TemporalEntity))
                    if opening_hours_description:
                        self.g.add((oh_ref, DCT.description, Literal(opening_hours_description)))
                    if opening_hours_frequency:
                        freq_ref = URIRef(opening_hours_frequency)
                        self.g.add((oh_ref, CV.frequency, freq_ref))
                        self._enrich_concept(freq_ref, predicate=DCT.accrualPeriodicity)

                if special_opening_hours_description or special_opening_hours_frequency:
                    soh_ref = BNode()
                    self.g.add((cp, CV.specialOpeningHoursSpecification, soh_ref))
                    self.g.add((soh_ref, RDF.type, TIME.TemporalEntity))
                    if special_opening_hours_description:
                        self.g.add((soh_ref, DCT.description, Literal(special_opening_hours_description)))
                    if special_opening_hours_frequency:
                        freq_ref = URIRef(special_opening_hours_frequency)
                        self.g.add((soh_ref, CV.frequency, freq_ref))
                        self._enrich_concept(freq_ref, predicate=DCT.accrualPeriodicity)

            log.debug(
                "[healthdcatap][serialize_agent] predicate=%s agent=%r normalized=%r",
                predicate,
                agent,
                {
                    "uri": agent_uri,
                    "name": name,
                    "type": type_uri,
                    "url": homepage,
                    "email": email,
                    "description": description,
                    "contact_page": contact_page,
                    "telephone": telephone,
                    "opening_hours_description": opening_hours_description,
                    "opening_hours_frequency": opening_hours_frequency,
                    "special_opening_hours_description": special_opening_hours_description,
                    "special_opening_hours_frequency": special_opening_hours_frequency,
                }
            )


    def _add_retention_period(self, subject_ref, retention_list):
        if not retention_list:
            return

        if isinstance(retention_list, dict):
            retention_list = [retention_list]

        first_valid = None
        for retention in retention_list:
            if not isinstance(retention, dict):
                continue
            start = retention.get("start")
            end = retention.get("end")
            comment = retention.get("comment")
            if start or end or comment:
                first_valid = retention
                break

        if not first_valid:
            return

        start = first_valid.get("start")
        end = first_valid.get("end")
        comment = first_valid.get("comment")

        period_node = BNode()
        self.g.add((subject_ref, HEALTHDCATAP.retentionPeriod, period_node))
        self.g.add((period_node, RDF.type, DCT.PeriodOfTime))
        if start:
            self.g.add((period_node, DCAT.startDate, Literal(start, datatype=XSD.date)))
        if end:
            self.g.add((period_node, DCAT.endDate, Literal(end, datatype=XSD.date)))
        if comment:
            self.g.add((period_node, RDFS.comment, Literal(comment)))

    def _add_nonneg_integer_triple(self, dataset_dict, dataset_ref, key, predicate):
        value = self._get_dict_value(dataset_dict, key)
        if value in (None, ""):
            return
        try:
            value = int(value)
            if value < 0:
                raise ValueError("Not a non-negative integer")
            self.g.add((dataset_ref, predicate, Literal(value, datatype=XSD.nonNegativeInteger)))
        except (TypeError, ValueError):
            self.g.add((dataset_ref, predicate, Literal(value)))

    def _add_quality_annotation(self, dataset_dict, dataset_ref):
        quality_annotation = self._get_dict_value(dataset_dict, "quality_annotation")
        if not quality_annotation:
            return

        if not isinstance(quality_annotation, list):
            quality_annotation = [quality_annotation]

        self._remove_predicate_objects(dataset_ref, DQV.hasQualityAnnotation)

        for annotation in quality_annotation:
            if not isinstance(annotation, dict):
                continue

            body = annotation.get("body")
            target = annotation.get("target")
            motivated_by = annotation.get("motivated_by")

            if not any([body, target, motivated_by]):
                continue

            annotation_ref = BNode()
            self.g.add((dataset_ref, DQV.hasQualityAnnotation, annotation_ref))
            self.g.add((annotation_ref, RDF.type, DQV.QualityCertificate))

            if self._is_uri(target):
                self.g.add((annotation_ref, OA.hasTarget, URIRef(target)))

            if self._is_uri(body):
                self.g.add((annotation_ref, OA.hasBody, URIRef(body)))

            if motivated_by:
                if self._is_uri(motivated_by):
                    self.g.add((annotation_ref, OA.motivatedBy, URIRef(motivated_by)))
                else:
                    self.g.add((annotation_ref, OA.motivatedBy, Literal(motivated_by)))
