import math
import random
from typing import Any, Dict, Optional, Tuple

PROGRAM_CREDIT_REQUIREMENTS = {
    "BBA": 9,
    "BBA in AIS": 9,
    "BSECO": 9,
    "BSCSE": 9,
    "BSEEE": 9,
    "BSDS": 9,
    "B.Sc. in CE": 9,
    "BSSEDS": 9,
    "BSSMSJ": 9,
    "BA in English": 9,
    "B.Pharm": 14,
    "BSBGE": 9,
}

GRADUATE_PROGRAMS = {
    "Graduate",
    "MBA",
    "EMBA",
    "MS",
    "MSc",
    "Masters",
}

PROGRAM_MODELS = {
    "engineering": {
        "base_tail": 0.14,
        "gamma": 1.48,
        "p_4": 0.007,
        "p_39": 0.022,
        "p_375": 0.065,
        "p_36": 0.105,
    },
    "business": {
        "base_tail": 0.16,
        "gamma": 1.42,
        "p_4": 0.010,
        "p_39": 0.025,
        "p_375": 0.070,
        "p_36": 0.115,
    },
    "pharmacy": {
        "base_tail": 0.15,
        "gamma": 1.40,
        "p_4": 0.008,
        "p_39": 0.024,
        "p_375": 0.068,
        "p_36": 0.110,
    },
    "humanities": {
        "base_tail": 0.15,
        "gamma": 1.45,
        "p_4": 0.009,
        "p_39": 0.023,
        "p_375": 0.066,
        "p_36": 0.108,
    },
    "graduate": {
        "base_tail": 0.22,
        "gamma": 1.30,
        "p_4": 0.025,
        "p_39": 0.055,
        "p_375": 0.120,
        "p_36": 0.180,
    },
}

MINIMUM_GPA = 3.50
SIMULATIONS = 10000


def normalize_program(program: Any) -> str:
    if program is None:
        return ""
    return str(program).strip()


def get_program_category(program: str) -> str:
    prog = normalize_program(program)
    if prog in GRADUATE_PROGRAMS:
        return "graduate"
    if prog == "B.Pharm":
        return "pharmacy"
    if prog in {"BBA", "BBA in AIS", "BSECO"}:
        return "business"
    if prog in {"BA in English", "BSSMSJ"}:
        return "humanities"
    return "engineering"


def get_minimum_credits(program: str) -> int:
    program = normalize_program(program)
    if program in PROGRAM_CREDIT_REQUIREMENTS:
        return PROGRAM_CREDIT_REQUIREMENTS[program]
    if program in GRADUATE_PROGRAMS:
        return 6
    return 9


def validate_eligibility(
    gpa: Any,
    program: Any,
    qualifying_credits: Any,
) -> Dict[str, Any]:
    try:
        gpa = float(gpa)
        qualifying_credits = float(qualifying_credits)
    except (TypeError, ValueError):
        return {
            "eligible": False,
            "reason": "invalid_input",
        }

    if not math.isfinite(gpa) or not math.isfinite(qualifying_credits):
        return {
            "eligible": False,
            "reason": "invalid_input",
        }

    if not 0.0 <= gpa <= 4.0:
        return {
            "eligible": False,
            "reason": "invalid_input",
        }

    if qualifying_credits <= 0:
        return {
            "eligible": False,
            "reason": "invalid_input",
        }

    minimum_credits = get_minimum_credits(program)

    if gpa < MINIMUM_GPA:
        return {
            "eligible": False,
            "reason": "gpa",
            "minimum_gpa": MINIMUM_GPA,
            "gpa": gpa,
            "minimum_credits": minimum_credits,
            "qualifying_credits": qualifying_credits,
        }

    if qualifying_credits < minimum_credits:
        return {
            "eligible": False,
            "reason": "credits",
            "minimum_credits": minimum_credits,
            "qualifying_credits": qualifying_credits,
            "gpa": gpa,
        }

    return {
        "eligible": True,
        "minimum_credits": minimum_credits,
        "qualifying_credits": qualifying_credits,
        "gpa": gpa,
    }


def estimate_higher_students_distribution(
    gpa: float,
    total_students: int,
    program: str,
    higher_students: Optional[int] = None,
) -> Tuple[float, float, bool]:
    total_students = max(10, int(total_students))
    gpa = max(3.50, min(4.00, float(gpa)))

    category = get_program_category(program)
    model = PROGRAM_MODELS[category]

    u = max(0.0, min(1.0, (4.00 - gpa) / 0.50))
    prior_frac = 0.0 if u <= 0.0 else model["base_tail"] * (u ** model["gamma"])

    mu_prior = prior_frac * total_students

    variance_binomial = total_students * max(0.005, prior_frac) * (1.0 - prior_frac)
    variability_batch = (total_students * 0.025) ** 2
    sigma_prior = math.sqrt(variance_binomial + variability_batch)
    sigma_prior = max(1.5, sigma_prior)

    if higher_students is not None:
        user_val = max(0, min(total_students - 1, int(higher_students)))
        sigma_user = max(2.0, user_val * 0.20)

        prec_prior = 1.0 / (sigma_prior ** 2)
        prec_user = 1.0 / (sigma_user ** 2)

        posterior_prec = prec_prior + prec_user
        mu_post = (prec_prior * mu_prior + prec_user * user_val) / posterior_prec
        sigma_post = math.sqrt(1.0 / posterior_prec)

        return (
            max(0.0, min(float(total_students - 1), mu_post)),
            max(1.0, sigma_post),
            True,
        )

    return (
        max(0.0, min(float(total_students - 1), mu_prior)),
        max(1.5, sigma_prior),
        False,
    )


def scholarship_bracket(
    position: int,
    total_students: int,
) -> str:
    position = max(1, int(position))
    total_students = max(1, int(total_students))

    top_2 = max(1, math.ceil(total_students * 0.02))
    top_6 = max(top_2, math.ceil(total_students * 0.06))
    top_10 = max(top_6, math.ceil(total_students * 0.10))

    if position <= top_2:
        return "100%"
    if position <= top_6:
        return "50%"
    if position <= top_10:
        return "25%"
    return "No Scholarship"


def run_monte_carlo_simulation(
    gpa: float,
    total_students: int,
    program: str,
    qualifying_credits: float,
    higher_students: Optional[int] = None,
    simulations: int = SIMULATIONS,
) -> Dict[str, Any]:
    total_students = max(10, int(total_students))
    simulations = max(2000, int(simulations))

    category = get_program_category(program)
    model = PROGRAM_MODELS[category]
    min_credits = get_minimum_credits(program)

    mu, sigma, used_user_estimate = estimate_higher_students_distribution(
        gpa=gpa,
        total_students=total_students,
        program=program,
        higher_students=higher_students,
    )

    credit_excess = max(0.0, float(qualifying_credits) - float(min_credits))
    credit_edge = min(1.5, (credit_excess / 12.0) * 1.0)

    top_2 = max(1, math.ceil(total_students * 0.02))
    top_6 = max(top_2, math.ceil(total_students * 0.06))
    top_10 = max(top_6, math.ceil(total_students * 0.10))

    outcomes = {
        "100%": 0,
        "50%": 0,
        "25%": 0,
        "No Scholarship": 0,
    }

    positions = []

    for _ in range(simulations):
        if gpa >= 4.00:
            expected_4s = max(1.0, total_students * model["p_4"])
            tied = max(1, round(random.gauss(expected_4s, math.sqrt(expected_4s))))
            pos = random.randint(1, tied)
            pos = max(1, round(pos - credit_edge * 0.5))
        else:
            sample_h = random.gauss(mu, sigma)
            sample_h = max(0, min(total_students - 1, round(sample_h)))
            pos = max(1, min(total_students, round(sample_h + 1 - credit_edge * 0.6)))

        positions.append(pos)

        if pos <= top_2:
            outcomes["100%"] += 1
        elif pos <= top_6:
            outcomes["50%"] += 1
        elif pos <= top_10:
            outcomes["25%"] += 1
        else:
            outcomes["No Scholarship"] += 1

    probabilities = {key: value / simulations for key, value in outcomes.items()}

    positions.sort()
    rank_p5 = positions[int(simulations * 0.05)]
    rank_p95 = positions[int(simulations * 0.95)]
    median_rank = positions[int(simulations * 0.50)]

    return {
        "probabilities": probabilities,
        "positions": positions,
        "rank_range": (rank_p5, rank_p95),
        "median_rank": median_rank,
        "cutoffs": {
            "top_2": top_2,
            "top_6": top_6,
            "top_10": top_10,
        },
        "used_user_estimate": used_user_estimate,
        "simulations": simulations,
    }


def calculate_confidence(
    total_students: int,
    higher_students: Optional[int],
    used_user_estimate: bool,
    probabilities: Dict[str, float],
) -> str:
    max_prob = max(probabilities.values())

    score = 0
    if total_students >= 150:
        score += 1
    if total_students >= 350:
        score += 1

    if higher_students is not None:
        score += 2
    elif used_user_estimate:
        score += 1

    if max_prob >= 0.75:
        score += 1

    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    return "Moderate"


def round_probability(probability: float) -> str:
    percentage = float(probability) * 100.0

    if percentage < 0.5:
        return "&lt;1%"
    if percentage >= 99.5:
        return "&gt;99%"

    rounded = int(round(percentage))
    return f"{rounded}%"


def most_likely_outcome(probabilities: Dict[str, float]) -> str:
    ordered = [
        "100%",
        "50%",
        "25%",
        "No Scholarship",
    ]
    return max(ordered, key=lambda k: probabilities.get(k, 0.0))


def generate_estimate(
    gpa: float,
    program: str,
    total_students: int,
    qualifying_credits: float,
    higher_students: Optional[int] = None,
) -> Dict[str, Any]:
    eligibility = validate_eligibility(
        gpa=gpa,
        program=program,
        qualifying_credits=qualifying_credits,
    )

    if not eligibility["eligible"]:
        return {
            "eligible": False,
            "eligibility": eligibility,
        }

    try:
        total_students = int(total_students)
        if total_students < 10:
            return {
                "eligible": False,
                "eligibility": {
                    "reason": "invalid_input",
                },
            }

        if higher_students is not None:
            higher_students = int(higher_students)
            if higher_students < 0 or higher_students >= total_students:
                return {
                    "eligible": False,
                    "eligibility": {
                        "reason": "higher_students",
                        "total_students": total_students,
                    },
                }

        simulation = run_monte_carlo_simulation(
            gpa=float(gpa),
            total_students=total_students,
            program=str(program),
            qualifying_credits=float(qualifying_credits),
            higher_students=higher_students,
            simulations=SIMULATIONS,
        )

        probabilities = simulation["probabilities"]

        confidence = calculate_confidence(
            total_students=total_students,
            higher_students=higher_students,
            used_user_estimate=simulation["used_user_estimate"],
            probabilities=probabilities,
        )

        rank_lo, rank_hi = simulation["rank_range"]
        pct_lo = max(0.1, round((rank_lo / total_students) * 100.0, 1))
        pct_hi = max(pct_lo, round((rank_hi / total_students) * 100.0, 1))

        any_scholarship_prob = (
            probabilities.get("100%", 0.0)
            + probabilities.get("50%", 0.0)
            + probabilities.get("25%", 0.0)
        )

        return {
            "eligible": True,
            "gpa": float(gpa),
            "program": normalize_program(program),
            "total_students": total_students,
            "qualifying_credits": float(qualifying_credits),
            "minimum_credits": eligibility["minimum_credits"],
            "higher_students": higher_students,
            "probabilities": probabilities,
            "display_probabilities": {
                key: round_probability(val) for key, val in probabilities.items()
            },
            "any_scholarship_prob": any_scholarship_prob,
            "confidence": confidence,
            "most_likely": most_likely_outcome(probabilities),
            "rank_range": (rank_lo, rank_hi),
            "percentile_range": (pct_lo, pct_hi),
            "cutoffs": simulation["cutoffs"],
            "simulations": simulation["simulations"],
            "estimate_source": (
                "user_estimate"
                if higher_students is not None
                else "statistical_estimate"
            ),
            "is_exact": False,
        }

    except Exception:
        return {
            "eligible": False,
            "eligibility": {
                "reason": "calculation_error",
            },
        }


def generate_result_text(result: Dict[str, Any]) -> str:
    gpa = result["gpa"]
    program = result["program"]
    total_students = result["total_students"]
    credits_val = result["qualifying_credits"]
    minimum_credits = result["minimum_credits"]
    probabilities = result["display_probabilities"]
    rank_lo, rank_hi = result["rank_range"]
    pct_lo, pct_hi = result["percentile_range"]
    most_likely = result["most_likely"]
    confidence = result["confidence"]
    cutoffs = result["cutoffs"]

    any_scholarship = result.get("any_scholarship_prob", 0.0)
    any_schol_text = round_probability(any_scholarship)

    source = result.get("estimate_source", "statistical_estimate")
    if source == "user_estimate":
        basis_info = "Bayesian calibration incorporating your estimated higher-GPA student count."
    else:
        basis_info = "Program-calibrated statistical distribution model with Monte Carlo simulation (10,000 iterations)."

    if rank_lo == rank_hi:
        rank_text = f"Rank ~{rank_lo}"
        pct_text = f"Top {pct_lo}%"
    else:
        rank_text = f"Rank {rank_lo} – {rank_hi}"
        pct_text = f"Top {pct_lo}% – {pct_hi}%"

    if credits_val > minimum_credits:
        credit_tip = (
            f"• <b>Credit Advantage:</b> Your {credits_val:g} credits exceed the "
            f"minimum required ({minimum_credits:g}), giving you an edge during rank ties."
        )
    else:
        credit_tip = (
            f"• <b>Credit Requirement:</b> You meet the minimum {minimum_credits:g} "
            "qualifying credits required for merit scholarship eligibility."
        )

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🎓 <b>UIU Merit Scholarship Estimate</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Trimester GPA:</b> {gpa:.2f}\n"
        f"<b>Academic Program:</b> {program}\n"
        f"<b>Batch Size:</b> ~{total_students} students\n"
        f"<b>Qualifying Credits:</b> {credits_val:g} <i>(Min: {minimum_credits:g})</i>\n\n"
        f"📊 <b>Estimated Standing:</b>\n"
        f"• Position: <b>{rank_text}</b> out of ~{total_students}\n"
        f"• Percentile: <b>{pct_text}</b>\n\n"
        "🏆 <b>Scholarship Chances:</b>\n"
        f"🥇 100% Waiver (Top 2%) → <b>{probabilities['100%']}</b>\n"
        f"🥈 50% Waiver (Top 6%)  → <b>{probabilities['50%']}</b>\n"
        f"🥉 25% Waiver (Top 10%) → <b>{probabilities['25%']}</b>\n"
        f"❌ No Scholarship       → <b>{probabilities['No Scholarship']}</b>\n\n"
        f"🎯 <b>Most Likely Outcome:</b> <b>{most_likely}</b>\n"
        f"✨ <b>Chance of Any Scholarship:</b> <b>{any_schol_text}</b>\n\n"
        f"📌 <b>Estimated Cutoffs (Batch ~{total_students}):</b>\n"
        f"• 100% Waiver: ~Top {cutoffs['top_2']} students\n"
        f"• 50% Waiver:  ~Top {cutoffs['top_6']} students\n"
        f"• 25% Waiver:  ~Top {cutoffs['top_10']} students\n\n"
        "💡 <b>Insights & Analysis:</b>\n"
        f"{credit_tip}\n"
        f"• <b>Confidence:</b> {confidence} ({basis_info})\n\n"
        "⚠️ <i>Disclaimer: This is an empirical statistical simulation based on UIU grading curves, not an official university ranking. Final decisions are made by UIU based on actual semester performance.</i>\n\n"
        "📌 <i>Scholarship excludes Thesis, Project, Internship, Retake, and Repeat courses.</i>"
    )


def generate_ineligible_text(eligibility: Dict[str, Any]) -> str:
    reason = eligibility.get("reason", "invalid_input")

    if reason == "gpa":
        return (
            "❌ <b>Not Eligible for Merit Scholarship</b>\n\n"
            f"Your previous trimester/semester GPA is "
            f"<b>{eligibility['gpa']:.2f}</b>, which is below "
            f"the minimum required GPA of "
            f"<b>{eligibility['minimum_gpa']:.2f}</b>.\n\n"
            "The top 10% ranking does not override the "
            "minimum GPA requirement."
        )

    if reason == "credits":
        return (
            "❌ <b>Minimum Credit Requirement Not Met</b>\n\n"
            f"Your qualifying credits: "
            f"<b>{eligibility['qualifying_credits']:g}</b>\n"
            f"Minimum required: "
            f"<b>{eligibility['minimum_credits']:g}</b>\n\n"
            "Based on the provided information, you do not "
            "meet the minimum credit requirement."
        )

    if reason == "higher_students":
        return (
            "⚠️ <b>Invalid Higher-GPA Estimate</b>\n\n"
            "The estimated number of students with a higher "
            "GPA must be smaller than the total program size."
        )

    if reason == "calculation_error":
        return (
            "⚠️ <b>Unable to Complete Estimate</b>\n\n"
            "The statistical calculation could not be completed "
            "right now. Please try again."
        )

    return (
        "⚠️ <b>Invalid Information</b>\n\n"
        "Please check your GPA, program and credit information "
        "and try again."
    )


def scholarship_rules_text() -> str:
    return (
        "🎓 <b>UIU Merit Scholarship Rules</b>\n\n"
        "🏆 <b>Scholarship Brackets</b>\n\n"
        "🥇 Top 2% → <b>100% Tuition Fee Waiver</b>\n"
        "🥈 Next 4% (Top 2%–6%) → <b>50% Tuition Fee Waiver</b>\n"
        "🥉 Next 4% (Top 6%–10%) → <b>25% Tuition Fee Waiver</b>\n\n"
        "📊 Approximately the top 10% may receive a merit "
        "scholarship, subject to eligibility requirements.\n\n"
        "📈 <b>Minimum GPA:</b> 3.50 in the just-previous "
        "trimester/semester.\n\n"
        "📚 <b>Minimum Qualifying Credits</b>\n\n"
        "BBA, BBA in AIS, BSECO, BSCSE, BSEEE, BSDS, "
        "B.Sc. in CE, BSSEDS, BSSMSJ, BA in English, "
        "BSBGE → 9 credits\n\n"
        "B.Pharm → 14 credits\n\n"
        "Graduate → 6 credits\n\n"
        "🚫 <b>Excluded Courses</b>\n"
        "Thesis, Project, Internship, Retake and Repeat "
        "courses are excluded from merit scholarship coverage.\n\n"
        "⚠️ The estimator is not an official UIU ranking "
        "or scholarship decision."
    )
