import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.models import (
    AdvocateProfile, ClientProfile, Case, Hearing, CaseNote, Task, FeeRecord,
)

DEMO_PASSWORD = "Legal@Demo123"


class Command(BaseCommand):
    help = "Populate the database with a realistic demo advocate, clients, cases, hearings, tasks and fees."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete existing demo data before seeding again.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Removing existing demo users and their data...")
            User.objects.filter(username__in=["advocate", "client", "client2"]).delete()

        advocate_user, created = User.objects.get_or_create(
            username="advocate",
            defaults={"first_name": "Aditi", "last_name": "Gupta", "email": "advocate@legaldesk.demo", "is_staff": True},
        )
        if created:
            advocate_user.set_password(DEMO_PASSWORD)
            advocate_user.is_superuser = True
            advocate_user.save()
        AdvocateProfile.objects.get_or_create(
            user=advocate_user, defaults={"bar_registration": "D/1234/2014", "phone": "+91 98100 00000", "law_firm": "Gupta & Associates"},
        )

        client_defs = [
            ("client", "Rajesh", "Sharma", "+91 98200 11111", "12 MG Road, Jaipur"),
            ("client2", "Neha", "Verma", "+91 98300 22222", "45 Civil Lines, Jaipur"),
        ]
        client_profiles = []
        for username, first, last, phone, address in client_defs:
            user, created = User.objects.get_or_create(
                username=username, defaults={"first_name": first, "last_name": last, "email": f"{username}@legaldesk.demo"},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            profile, _ = ClientProfile.objects.get_or_create(user=user, defaults={"phone": phone, "address": address})
            client_profiles.append(profile)

        if Case.objects.filter(advocate=advocate_user).exists():
            self.stdout.write(self.style.WARNING("Demo cases already exist for 'advocate' — skipping case creation."))
        else:
            today = timezone.localdate()
            cases_data = [
                dict(case_number="LD-2026-001", title="Sharma vs. State", case_type="Criminal", court="District Court, Jaipur",
                     opposite_party="State of Rajasthan", status="HEARING", client=client_profiles[0],
                     description="Bail application and trial proceedings following an alleged property dispute escalation."),
                dict(case_number="LD-2026-002", title="Verma Divorce Petition", case_type="Family", court="Family Court, Jaipur",
                     opposite_party="Mr. Verma", status="ACTIVE", client=client_profiles[1],
                     description="Mutual consent divorce petition with contested child custody arrangement."),
                dict(case_number="LD-2026-003", title="Sharma Property Dispute", case_type="Civil", court="Civil Court, Jaipur",
                     opposite_party="Amit Gupta", status="PENDING", client=client_profiles[0],
                     description="Boundary dispute over ancestral property; awaiting survey report from the court commissioner."),
                dict(case_number="LD-2025-114", title="Verma Consumer Complaint", case_type="Consumer", court="District Consumer Forum",
                     opposite_party="ABC Builders Pvt. Ltd.", status="CLOSED", client=client_profiles[1],
                     description="Compensation claim for delayed possession, settled in the client's favour."),
            ]
            cases = []
            for cd in cases_data:
                case = Case.objects.create(advocate=advocate_user, **cd)
                cases.append(case)

            hearing_offsets = [3, 6, 10, -8, -20]
            for i, case in enumerate(cases[:3]):
                for j, offset in enumerate(hearing_offsets[:3]):
                    Hearing.objects.create(
                        case=case,
                        hearing_date=today + datetime.timedelta(days=offset + i * 2),
                        purpose="Arguments" if j == 0 else ("Evidence" if j == 1 else "Next Date of Hearing"),
                        notes="Court to hear both parties on outstanding applications." if j == 0 else "",
                        client_visible=True,
                    )

            CaseNote.objects.create(case=cases[0], author=advocate_user, note="Discussed bail strategy with client; arranging surety documents.", private=True)
            CaseNote.objects.create(case=cases[1], author=advocate_user, note="Client open to mediation on custody schedule — propose alternate weekends.", private=True)

            Task.objects.create(assigned_to=advocate_user, case=cases[0], title="File bail application", priority="HIGH", due_date=today + datetime.timedelta(days=2))
            Task.objects.create(assigned_to=advocate_user, case=cases[1], title="Prepare custody affidavit", priority="MEDIUM", due_date=today + datetime.timedelta(days=5))
            Task.objects.create(assigned_to=advocate_user, case=cases[2], title="Follow up on survey report", priority="LOW", due_date=today - datetime.timedelta(days=1))
            Task.objects.create(assigned_to=advocate_user, case=None, title="Renew chamber bar association membership", priority="LOW", due_date=today + datetime.timedelta(days=20))

            FeeRecord.objects.create(case=cases[0], amount=25000, description="Retainer fee", paid=True)
            FeeRecord.objects.create(case=cases[0], amount=15000, description="Bail application charges", paid=False)
            FeeRecord.objects.create(case=cases[1], amount=40000, description="Filing + first hearing fee", paid=True)
            FeeRecord.objects.create(case=cases[2], amount=10000, description="Consultation fee", paid=False)
            FeeRecord.objects.create(case=cases[3], amount=30000, description="Full settlement fee", paid=True)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Log in with:"))
        self.stdout.write(f"  Advocate → username: advocate   password: {DEMO_PASSWORD}")
        self.stdout.write(f"  Client   → username: client     password: {DEMO_PASSWORD}")
