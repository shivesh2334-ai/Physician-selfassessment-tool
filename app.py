import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import traceback

# Page configuration
st.set_page_config(
    page_title="Physician Self-Assessment Tool",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with improved accessibility
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .category-header {
        font-size: 1.8rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .score-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin: 1rem 0;
    }
    .recommendation {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    .warning {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
    .stButton button {
        width: 100%;
    }
    .stRadio > div {
        flex-direction: column;
        align-items: flex-start;
    }
    .stRadio > div[role="radiogroup"] > label {
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
    }
    .stRadio > div[role="radiogroup"] > label:hover {
        background-color: #f8f9fa;
    }
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .category-header {
            font-size: 1.5rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Assessment questions
QUESTIONS = {
    "Personal Connect (Do You Care About Me?)": [
        {
            "question": "How often do you call patients by name and make personal contact?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.2  # Weight factor for importance
        },
        {
            "question": "Do you sit down with patients (not standing) during consultations?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.0
        },
        {
            "question": "How frequently do you telephone patients to check on them after procedures or missed appointments?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.1
        },
        {
            "question": "Do you show empathy and listen actively to patients' stories?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.3
        },
        {
            "question": "How often do you discuss patients' personal life, hobbies, likes, and dislikes?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.0
        }
    ],
    "Trust of Your Trade (Are You the Best?)": [
        {
            "question": "How regularly do you attend lectures and national meetings?",
            "options": ["Never", "Once a year", "2-3 times/year", "Quarterly", "Monthly or more"],
            "weight": 1.0
        },
        {
            "question": "How often do you read the latest research in your area of practice?",
            "options": ["Never", "Rarely", "Monthly", "Weekly", "Daily"],
            "weight": 1.2
        },
        {
            "question": "Do you pursue continuing medical education and skill development?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Consistently"],
            "weight": 1.1
        },
        {
            "question": "How confident are you in acknowledging when you need refreshers in certain areas?",
            "options": ["Not confident", "Slightly confident", "Moderately confident", "Very confident", "Extremely confident"],
            "weight": 1.0
        },
        {
            "question": "Do you strive for excellence beyond just avoiding malpractice?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.3
        }
    ],
    "Social Trust (Can I Trust You?)": [
        {
            "question": "How much time do you invest in building trust with patients from different backgrounds?",
            "options": ["No effort", "Minimal effort", "Moderate effort", "Significant effort", "Maximum effort"],
            "weight": 1.2
        },
        {
            "question": "Do you create a safe environment for patients to share sensitive issues (substance use, mental health)?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.3
        },
        {
            "question": "How reliable are you in following up on patient concerns?",
            "options": ["Unreliable", "Somewhat reliable", "Moderately reliable", "Very reliable", "Completely reliable"],
            "weight": 1.1
        },
        {
            "question": "Do you demonstrate care about patients' wellbeing in your actions?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.2
        },
        {
            "question": "How well do you encourage patients to share when they're feeling sad, depressed, or lonely?",
            "options": ["Not at all", "Poorly", "Adequately", "Well", "Excellently"],
            "weight": 1.0
        }
    ],
    "Treating Style (Are You Treating Me Differently?)": [
        {
            "question": "How conscious are you of health disparities affecting different populations?",
            "options": ["Not conscious", "Slightly conscious", "Moderately conscious", "Very conscious", "Extremely conscious"],
            "weight": 1.1
        },
        {
            "question": "Do you examine your own biases regarding race, ethnicity, sex, or socioeconomic status?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Regularly"],
            "weight": 1.3
        },
        {
            "question": "How carefully do you ensure equitable treatment across all patient demographics?",
            "options": ["Not carefully", "Somewhat carefully", "Moderately carefully", "Very carefully", "Extremely carefully"],
            "weight": 1.2
        },
        {
            "question": "Do you stay informed about social determinants of health?",
            "options": ["Not informed", "Slightly informed", "Moderately informed", "Well informed", "Expert level"],
            "weight": 1.0
        },
        {
            "question": "How often do you reflect on whether you might be perceived as judging patients?",
            "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "weight": 1.1
        }
    ]
}

# Function to calculate weighted scores
def calculate_scores(responses):
    """Calculate category and overall scores with weighted questions."""
    try:
        category_scores = {}
        category_details = {}
        
        for category, answers in responses.items():
            total_weighted = 0
            max_weighted = 0
            question_scores = []
            
            for i, answer in enumerate(answers):
                weight = QUESTIONS[category][i]["weight"]
                weighted_score = answer * weight
                total_weighted += weighted_score
                max_weighted += 4 * weight  # Max answer is 4
                question_scores.append({
                    "question": QUESTIONS[category][i]["question"],
                    "score": answer,
                    "max_score": 4,
                    "weighted_score": weighted_score
                })
            
            # Calculate normalized score (0-5 scale)
            normalized_score = (total_weighted / max_weighted) * 5 if max_weighted > 0 else 0
            category_scores[category] = round(normalized_score, 2)
            category_details[category] = {
                "raw_score": total_weighted,
                "max_possible": max_weighted,
                "normalized_score": normalized_score,
                "question_details": question_scores
            }
        
        # Calculate overall score (weighted average)
        overall_score = sum(category_scores.values()) / len(category_scores) if category_scores else 0
        overall_score = round(overall_score, 2)
        
        return category_scores, overall_score, category_details
        
    except Exception as e:
        st.error(f"Error calculating scores: {str(e)}")
        st.error(traceback.format_exc())
        return {}, 0, {}

def get_recommendations(category_scores, overall_score):
    """Generate personalized recommendations based on scores."""
    try:
        recommendations = []
        
        # Overall assessment
        if overall_score >= 4.5:
            recommendations.append({
                "level": "Excellent",
                "message": "You demonstrate exceptional patient-centered care across all dimensions. Continue your excellent work!",
                "icon": "🎯"
            })
        elif overall_score >= 4.0:
            recommendations.append({
                "level": "Very Good",
                "message": "You show strong patient care skills with minor areas for enhancement.",
                "icon": "👍"
            })
        elif overall_score >= 3.5:
            recommendations.append({
                "level": "Good",
                "message": "You have good patient care skills. Focus on the areas below to reach excellence.",
                "icon": "📈"
            })
        elif overall_score >= 3.0:
            recommendations.append({
                "level": "Fair",
                "message": "You have a foundation to build on. Improvement needed in several areas.",
                "icon": "⚠️"
            })
        else:
            recommendations.append({
                "level": "Needs Improvement",
                "message": "Your patient care approach needs substantial development. Prioritize the recommendations below.",
                "icon": "🚨"
            })
        
        # Category-specific recommendations
        improvement_categories = [cat for cat, score in category_scores.items() if score < 4.0]
        
        if improvement_categories:
            recommendations.append({
                "level": "Focus Areas",
                "message": f"Priority areas for improvement: {', '.join([c.split('(')[0].strip() for c in improvement_categories])}",
                "icon": "🎯"
            })
        
        # Detailed recommendations for each category
        for category, score in category_scores.items():
            if score < 4.0:
                if "Personal Connect" in category:
                    recommendations.append({
                        "category": category,
                        "score": score,
                        "actions": [
                            "Make it a habit to sit down during all patient consultations",
                            "Call patients by name and ask about their personal interests at each visit",
                            "Set calendar reminders to follow up with patients after procedures",
                            "Practice active listening - allow 2-3 seconds of silence after patients speak",
                            "Schedule 5-10 extra minutes for new patient appointments"
                        ]
                    })
                elif "Trust of Your Trade" in category:
                    recommendations.append({
                        "category": category,
                        "score": score,
                        "actions": [
                            "Subscribe to 2-3 key journals in your specialty",
                            "Register for at least 2 conferences per year with action plan implementation",
                            "Join or start a journal club with colleagues",
                            "Dedicate 30 minutes weekly to reading latest research (Friday afternoons work well)",
                            "Complete 25+ CME credits annually focused on clinical practice gaps"
                        ]
                    })
                elif "Social Trust" in category:
                    recommendations.append({
                        "category": category,
                        "score": score,
                        "actions": [
                            "Use the BATHE technique (Background, Affect, Trouble, Handling, Empathy) for sensitive topics",
                            "Start appointments with 'What's most important for us to discuss today?'",
                            "Create a checklist for following up on every patient concern",
                            "Practice reflective statements: 'What I hear you saying is...'",
                            "Document patient preferences and follow up on them at next visit"
                        ]
                    })
                elif "Treating Style" in category:
                    recommendations.append({
                        "category": category,
                        "score": score,
                        "actions": [
                            "Complete implicit bias training annually",
                            "Review practice data annually for demographic treatment patterns",
                            "Use the SAFETIPS mnemonic (Sex, Age, Faith, Ethnicity, Trauma, Identity, Personality, Status) in patient assessments",
                            "Partner with community organizations to understand local health determinants",
                            "Regularly audit your own clinical decisions for consistency across patient groups"
                        ]
                    })
        
        return recommendations
        
    except Exception as e:
        st.error(f"Error generating recommendations: {str(e)}")
        return []

def create_score_chart(category_scores):
    """Create bar chart visualization of scores."""
    try:
        categories = list(category_scores.keys())
        scores = list(category_scores.values())
        
        # Shorten category names for display
        short_categories = [
            "Personal\nConnect",
            "Trust of\nTrade",
            "Social\nTrust",
            "Treating\nStyle"
        ]
        
        fig = go.Figure()
        
        # Add bar chart
        fig.add_trace(go.Bar(
            x=short_categories,
            y=scores,
            marker_color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'],
            text=[f'{score:.2f}' for score in scores],
            textposition='outside',
            hovertext=[f'{cat}: {score:.2f}/5.0' for cat, score in zip(categories, scores)],
            hoverinfo='text'
        ))
        
        # Add reference lines
        fig.add_hline(y=4.0, line_dash="dash", line_color="green", 
                      annotation_text="Target (4.0)", annotation_position="right")
        fig.add_hline(y=3.0, line_dash="dot", line_color="orange", 
                      annotation_text="Baseline (3.0)", annotation_position="right")
        
        fig.update_layout(
            title="Professional Score by Category",
            yaxis_title="Score (0-5 scale)",
            yaxis_range=[0, 5.5],
            height=450,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        
        fig.update_xaxes(tickangle=0)
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return go.Figure()

def create_radar_chart(category_scores):
    """Create radar chart visualization."""
    try:
        categories = ["Personal\nConnect", "Trust of\nTrade", "Social\nTrust", "Treating\nStyle"]
        scores = list(category_scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],  # Close the polygon
            theta=categories + [categories[0]],
            fill='toself',
            name='Your Scores',
            line_color='#3498db',
            fillcolor='rgba(52, 152, 219, 0.3)'
        ))
        
        # Add target score reference
        fig.add_trace(go.Scatterpolar(
            r=[4, 4, 4, 4, 4],
            theta=categories + [categories[0]],
            fill='toself',
            name='Target Score',
            line_color='#2ecc71',
            fillcolor='rgba(46, 204, 113, 0.1)',
            opacity=0.5
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickvals=[0, 1, 2, 3, 4, 5],
                    ticktext=['0', '1', '2', '3', '4', '5']
                ),
                angularaxis=dict(
                    direction="clockwise"
                )
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=450,
            title="Professional Profile Radar",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating radar chart: {str(e)}")
        return go.Figure()

def create_progress_timeline():
    """Create a simple progress timeline visualization."""
    fig = go.Figure()
    
    milestones = [
        {"stage": "Assessment", "progress": 100, "status": "Complete"},
        {"stage": "Analysis", "progress": 100, "status": "Complete"},
        {"stage": "Action Plan", "progress": 75, "status": "In Progress"},
        {"stage": "Implementation", "progress": 25, "status": "Not Started"},
        {"stage": "Re-assessment", "progress": 0, "status": "Not Started"}
    ]
    
    stages = [m["stage"] for m in milestones]
    progress = [m["progress"] for m in milestones]
    colors = ['#2ecc71' if p == 100 else '#f39c12' if p > 0 else '#e74c3c' for p in progress]
    
    fig.add_trace(go.Bar(
        x=stages,
        y=progress,
        marker_color=colors,
        text=[f'{p}%' for p in progress],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Professional Development Progress",
        yaxis_title="Completion (%)",
        yaxis_range=[0, 110],
        height=300,
        showlegend=False
    )
    
    return fig

def validate_responses(responses):
    """Validate that all questions have been answered."""
    missing = []
    for category, answers in responses.items():
        for i, answer in enumerate(answers):
            if answer is None:
                missing.append(f"{category}: Question {i+1}")
    return missing

def export_to_excel(category_scores, overall_score, category_details, responses):
    """Create Excel file with detailed results."""
    try:
        # Create DataFrames for different sheets
        summary_data = {
            'Category': list(category_scores.keys()),
            'Score (0-5)': list(category_scores.values()),
            'Assessment Date': [datetime.now().strftime('%Y-%m-%d')] * len(category_scores)
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Detailed question-by-question data
        detailed_data = []
        for category, details in category_details.items():
            for q_detail in details['question_details']:
                detailed_data.append({
                    'Category': category,
                    'Question': q_detail['question'],
                    'Raw Score': q_detail['score'],
                    'Max Score': q_detail['max_score'],
                    'Weighted Score': round(q_detail['weighted_score'], 2),
                    'Percentage': round((q_detail['score'] / q_detail['max_score']) * 100, 1)
                })
        detailed_df = pd.DataFrame(detailed_data)
        
        # Recommendations
        recommendations = get_recommendations(category_scores, overall_score)
        rec_data = []
        for rec in recommendations:
            if 'actions' in rec:
                for action in rec['actions']:
                    rec_data.append({
                        'Category': rec.get('category', 'General'),
                        'Priority': 'High' if rec.get('score', 5) < 3.0 else 'Medium',
                        'Action Item': action
                    })
        rec_df = pd.DataFrame(rec_data) if rec_data else pd.DataFrame({'Note': ['No specific recommendations needed']})
        
        # Create Excel writer
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            detailed_df.to_excel(writer, sheet_name='Detailed Scores', index=False)
            rec_df.to_excel(writer, sheet_name='Action Plan', index=False)
            
            # Add overall score sheet
            overall_df = pd.DataFrame({
                'Metric': ['Overall Score', 'Assessment Date', 'Total Questions Answered'],
                'Value': [f"{overall_score}/5.0", datetime.now().strftime('%Y-%m-%d %H:%M'), len(detailed_data)]
            })
            overall_df.to_excel(writer, sheet_name='Overview', index=False)
        
        output.seek(0)
        return output
        
    except Exception as e:
        st.error(f"Error creating Excel file: {str(e)}")
        return None

# Main application
def main():
    try:
        # Title and introduction
        st.markdown('<h1 class="main-header">🏥 Physician Professional Self-Assessment Tool</h1>', unsafe_allow_html=True)
        
        # Sidebar for additional options
        with st.sidebar:
            st.markdown("### 📊 About This Tool")
            st.info("""
            Based on **"5 Questions Patients Have but Never Ask"** (JAMA Neurology, 2018).
            
            This assessment helps physicians evaluate patient-centered care across four critical dimensions of trust and connection.
            
            **Scoring:** Each question is scored 0-4, converted to a 0-5 scale with weighted importance.
            """)
            
            st.markdown("### 📈 Interpretation Guide")
            st.markdown("""
            - **4.5-5.0**: Exceptional practice
            - **4.0-4.5**: Strong performance
            - **3.5-4.0**: Good with room for growth
            - **3.0-3.5**: Foundation established
            - **<3.0**: Needs development
            """)
            
            if st.session_state.get('submitted', False):
                if st.button("🔄 Start New Assessment", use_container_width=True):
                    st.session_state.submitted = False
                    st.session_state.responses = {}
                    st.rerun()
        
        # Main content area
        tab1, tab2, tab3 = st.tabs(["📝 Assessment", "📊 Results", "📋 Action Plan"])
        
        with tab1:
            st.markdown("""
            ### Assessment Instructions
            
            1. **Read each question carefully**
            2. **Rate yourself honestly** using the 5-point scale
            3. **Complete all questions** before submitting
            4. **Review your personalized results** and action plan
            
            *Scale: 0 (Lowest/Never) to 4 (Highest/Always)*
            """)
            
            # Initialize session state
            if 'responses' not in st.session_state:
                st.session_state.responses = {}
            if 'submitted' not in st.session_state:
                st.session_state.submitted = False
            
            # Assessment form
            if not st.session_state.submitted:
                with st.form("assessment_form"):
                    st.markdown("---")
                    
                    for category, questions in QUESTIONS.items():
                        st.markdown(f'<div class="category-header">{category}</div>', unsafe_allow_html=True)
                        
                        category_responses = []
                        for i, q in enumerate(questions):
                            col1, col2 = st.columns([3, 2])
                            with col1:
                                response = st.radio(
                                    f"**Q{i+1}:** {q['question']}",
                                    options=range(len(q["options"])),
                                    format_func=lambda x, opts=q["options"]: f"{x} - {opts[x]}",
                                    key=f"{category}_{i}",
                                    help=f"Importance weight: {q['weight']}x"
                                )
                            with col2:
                                st.caption(f"**Scale:**")
                                for idx, opt in enumerate(q["options"]):
                                    st.caption(f"{idx}: {opt}")
                            
                            category_responses.append(response)
                            if i < len(questions) - 1:
                                st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
                        
                        st.session_state.responses[category] = category_responses
                        st.markdown("---")
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        submitted = st.form_submit_button(
                            "📊 Calculate My Professional Score",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    if submitted:
                        # Validate all questions answered
                        missing = validate_responses(st.session_state.responses)
                        if missing:
                            st.error(f"Please answer all questions. Missing: {', '.join(missing[:3])}")
                            if len(missing) > 3:
                                st.error(f"... and {len(missing)-3} more")
                        else:
                            st.session_state.submitted = True
                            st.rerun()
        
        with tab2:
            if st.session_state.get('submitted', False):
                # Calculate scores
                category_scores, overall_score, category_details = calculate_scores(st.session_state.responses)
                
                # Display results
                st.markdown("## 📊 Assessment Results")
                
                # Overall score card
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    score_color = "#2ecc71" if overall_score >= 4.0 else "#f39c12" if overall_score >= 3.0 else "#e74c3c"
                    st.markdown(f"""
                    <div class="score-card" style="text-align: center; border-left-color: {score_color};">
                        <h2>Overall Professional Score</h2>
                        <h1 style="color: {score_color}; font-size: 4rem; margin: 0;">{overall_score:.2f}</h1>
                        <h3 style="color: #7f8c8d;">out of 5.0</h3>
                        <p style="font-size: 1.2rem; margin-top: 1rem;">
                            <strong>Assessment Date:</strong> {datetime.now().strftime('%B %d, %Y')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Visualizations
                st.markdown("### 📈 Score Visualizations")
                viz_col1, viz_col2 = st.columns(2)
                
                with viz_col1:
                    st.plotly_chart(create_score_chart(category_scores), 
                                  use_container_width=True,
                                  config={'displayModeBar': True})
                
                with viz_col2:
                    st.plotly_chart(create_radar_chart(category_scores), 
                                  use_container_width=True,
                                  config={'displayModeBar': True})
                
                st.markdown("---")
                
                # Category breakdown
                st.markdown("### 📋 Category Breakdown")
                
                cols = st.columns(4)
                colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
                
                for i, (category, score) in enumerate(category_scores.items()):
                    with cols[i]:
                        short_name = category.split("(")[0].strip()
                        color = colors[i]
                        score_color = "#2ecc71" if score >= 4.0 else "#f39c12" if score >= 3.0 else "#e74c3c"
                        
                        st.markdown(f"""
                        <div style="background-color: {color}; padding: 1rem; border-radius: 10px; 
                                   text-align: center; color: white; margin-bottom: 0.5rem;">
                            <h4 style="margin: 0; color: white;">{short_name}</h4>
                        </div>
                        <div style="background-color: white; padding: 1rem; border-radius: 0 0 10px 10px; 
                                   border: 2px solid {color}; border-top: none; text-align: center;">
                            <h2 style="margin: 0.5rem 0; color: {score_color};">{score:.2f}/5.0</h2>
                            <p style="margin: 0; font-size: 0.9rem; color: #666;">
                                {category_details[category]['raw_score']:.1f} / {category_details[category]['max_possible']:.1f} weighted
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Detailed scores expander
                with st.expander("📝 View Detailed Question Scores"):
                    for category, details in category_details.items():
                        st.markdown(f"**{category}**")
                        df = pd.DataFrame(details['question_details'])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                
            else:
                st.info("👈 Please complete the assessment in the 'Assessment' tab to see your results.")
        
        with tab3:
            if st.session_state.get('submitted', False):
                # Get recommendations
                recommendations = get_recommendations(category_scores, overall_score)
                
                st.markdown("## 🎯 Personalized Action Plan")
                
                # Overall recommendation
                if recommendations:
                    st.markdown(f"""
                    <div class="recommendation">
                        <h3>{recommendations[0]['icon']} Overall Assessment: {recommendations[0]['level']}</h3>
                        <p>{recommendations[0]['message']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Category-specific recommendations
                st.markdown("### 📝 Improvement Areas & Actions")
                
                for rec in recommendations[1:]:
                    if 'category' in rec:
                        with st.expander(f"🎯 {rec['category'].split('(')[0].strip()} - Score: {rec['score']:.2f}/5.0"):
                            st.markdown(f"**Priority Level:** {'High' if rec['score'] < 3.0 else 'Medium'}")
                            st.markdown("**Recommended Actions:**")
                            for i, action in enumerate(rec['actions'], 1):
                                st.markdown(f"{i}. {action}")
                    
                    elif 'level' in rec and rec['level'] == 'Focus Areas':
                        st.markdown(f"""
                        <div class="warning">
                            <h4>{rec['icon']} {rec['level']}</h4>
                            <p>{rec['message']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Progress timeline
                st.markdown("### 📅 Implementation Timeline")
                st.plotly_chart(create_progress_timeline(), use_container_width=True)
                
                # Export options
                st.markdown("---")
                st.markdown("### 💾 Export Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # JSON export
                    results = {
                        "timestamp": datetime.now().isoformat(),
                        "overall_score": overall_score,
                        "category_scores": category_scores,
                        "category_details": category_details,
                        "responses": st.session_state.responses
                    }
                    
                    st.download_button(
                        label="📥 Download JSON",
                        data=json.dumps(results, indent=2),
                        file_name=f"physician_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col2:
                    # Excel export
                    excel_data = export_to_excel(category_scores, overall_score, category_details, 
                                               st.session_state.responses)
                    if excel_data:
                        st.download_button(
                            label="📊 Download Excel Report",
                            data=excel_data,
                            file_name=f"physician_assessment_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                # Reset button
                st.markdown("---")
                if st.button("🔄 Take Assessment Again", use_container_width=True, type="secondary"):
                    st.session_state.submitted = False
                    st.session_state.responses = {}
                    st.rerun()
            
            else:
                st.info("👈 Complete the assessment to generate your personalized action plan.")
    
    except Exception as e:
        st.error("An error occurred while running the application.")
        st.error(f"Error details: {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
    main()
