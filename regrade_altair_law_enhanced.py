#!/usr/bin/env python3

import pandas as pd
from supabase_database import SupabaseDatabase
import json

def get_manual_output():
    """Return the manual extraction output for comparison"""
    return [
        {
            "response_id": "Altair Law_Cyrus Nazarian_1_1",
            "subject": "Evaluation of Rev for Legal Investigations",
            "question": "What prompted an evaluation of a tool like Rev? Were you using something else beforehand or was it a new tool for the company?",
            "verbatim_response": "I think I'm the only one that's really using it right now, so I wouldn't say it's for the firm yet. I've been using it and to test it out and see if it's something that I should push to have more widespread adoption. But part of it for me is that historically, either we need to find a vendor who we send files to, and then they do human transcription services, and it takes time. It's expensive. And I would rather, while doing an investigation, upload a series of videos, audio files, and then within minutes, have audio transcription, an actual transcript ready. And have it mostly be. I mean, accuracy is important with this. So every time I've used it, I've needed to go through and edit, do some extensive editing. Because we need as faithful a recreation as possible. Faithful transcription as possible. So yeah. I think it's the speed and expense that really turned me on to it. Yeah, it lets me just get work done in a more timely manner instead of waiting and then checking emails with some other service and be like, is it ready yet? It's frustrating."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_1_2",
            "subject": "Use Cases for Rev Transcription",
            "question": "Do you mind touching on any of the areas specifically that you've used transcription for?",
            "verbatim_response": "So in the work that we do, we have, some of the first things I use this for was a 911 call. 911 call, audio file. That was an interview conducted by an insurance company of our client. So I wanted to understand, okay, what was without having to rehear or then transcribe the 911 call or the interview, know exactly what was said and by whom. Also used it for interviews conducted of a criminal defendant by law enforcement. Using that was originally on body worn camera footage. So it was some lengthy interviewing and I wanted to have that just memorialized. I've written and during a case evaluation we are collecting facts, all the facts we possibly can. So for preserving or understanding what the facts are and not having to just rewatch audio or listen to a story, rewatch video, or listen to audio. This is nice because then you have keyword search and you can get summaries and go from there for understanding the whole factual universe of the case."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_2_1",
            "subject": "Vendor Selection Process",
            "question": "When you went to find a vendor, did you already know about Rev, or did you look at a few different vendors online through search?",
            "verbatim_response": "I first learned to read from a prior firm I was with and then I did some research on Rev and its competitors. I can't remember the name of any competitors, but from what I was able, what I recall is that you guys were quite competitive with the rest of the field, and I generally like the layout and how the workflow goes, so I thought that was cool."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_2_2",
            "subject": "Evaluation Criteria",
            "question": "Speed and cost were your top two priority. And you just mentioned layout as kind of a nice to have something that made you feel comfortable in it. Were there any other criteria that you evaluated when comparing Rev to other vendors?",
            "verbatim_response": "Well, accuracy is important. The accuracy was one of the. So speed cost accuracy. And because ultimately less accuracy is less speed. So you can spit out a transcript really fast. But if I still have to go and spend, you know, 45 minutes on an hour long interview to make sure that everything that's in the transcript is accurately reflects what was said, then, you know, that's not ideal. I've had to do that. But so I don't know how I don't know how your product compares in accuracy to others."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_2_3",
            "subject": "Legal-Specific Requirements",
            "question": "When it comes to the transcription work they had done, were there any needs or even criteria that were specific to legal? We should be aware of formatting, for example, or any way that you looked at data. Obviously accuracy is important, but anything specific to legal.",
            "verbatim_response": "I'd say because say for instance, we have a transcript of a we uploaded an audio file of a recording of a medical examination. Is your is Rev SOC two compliant, HIPAA compliant. So privacy considerations are definitely important. In the legal context so that we don't inadvertently divulge attorney client privilege communications or violate our privacy rights in medical records or otherwise. That's quite important."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_3_1",
            "subject": "Performance Evaluation",
            "question": "How did Rev do on these items? Like how did do they meet your expectations on these items fall short. Did they exceed.",
            "verbatim_response": "Speed I think exceeded my expectations. But the thing is, like, I would sacrifice speed for better accuracy. Gladly. If it took twice as long. Three times as like, I think it's done like a 45 minute file audio file in like seven minutes. Even if it took an hour, I'd be happy to to to sacrifice speed for accuracy. Yeah. Costs, I think is fine, right? It's fine. Because if it were with the given, with the current accuracy, I'd have a hard time justifying a greater cost because of how much work I've had to do. Editing the transcript to have it be a faithful transcript. So I think sacrificing speed in the interest of accuracy at the current cost would make sense. But if in future there's a way to. So yeah, speed exceeded my expectations. Cost my expectations. Accuracy fell below my expectations. Data security and compliance met expectations. Ease of use. Once I figured out how, you know, double clicking that you can essentially treat it like a word doc. Kind of ease of use more or less met my expectations, maybe just a little bit under under my expectations. And then, I don't know, I, I guess I'd have to know what specific features you'd be referring to to, I guess specific features. Let's see. So if we were to download okay, this is cool how you have the inline captions columns. And then I like that they're a word doc and PDF and text file that you can export. Highlighted sections only include inline timestamps. I like those features I guess, expectations with regard to specific features."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_3_2",
            "subject": "Human Transcription Use Cases",
            "question": "With accuracy rating so high. Are there any files where it would be worth it to upgrade to a human transcriptionist first for accuracy purposes?",
            "verbatim_response": "So that's something that I haven't done yet. It's something that I believe I would do if I was I was planning on doing that for a case. I was going to head to trial, but it resolved, so there's no need to anymore. But I, I was curious when it comes to getting a human transcription. What is Rev's litigation support and ensuring that whoever did the transcription can provide like an attestation, like an affidavit or attestation or declaration or appear for, for the purposes of trial to authenticate the transcript."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_4_1",
            "subject": "Transcription Usage",
            "question": "How do you use the transcriptions after you've received them?",
            "verbatim_response": "I I read through them. I read through them. To collect information from them about the facts of the accident. I mean, I get quite a bit when I'm going editing the transcript while watching or listening to the file. But I use it in case evaluations. I use it in building the factual background of the case, fleshing that out. I use it to collect witness statements. Again, for factual background, which will then let me do a liability analysis, get an idea of injuries."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_4_2",
            "subject": "Transcription Review Process",
            "question": "Do you read through the transcriptions in Rev or move them to a word doc?",
            "verbatim_response": "I think for me, the ones that I've edited, I by the time I've read through it, I have a pretty good grasp of what's going on. That I don't really need to read through the transcript once it's produced. But I do print it and save it, and we'll then send it to Extended to other attorneys with my evaluation and saying, hey, this is what's in here. Here's a quick summary. And this this is I will, I'll do is say, you know, that this person A stated this at the three minute 32nd mark, and I'll cite to it so that they can go back and either watch the video or review the transcript or both."
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_5_1",
            "subject": "Product Features",
            "question": "What features would be compelling for a legal-specific package from Rev?",
            "verbatim_response": "Just based on you have the regular formats that you give. But I would look into more of, , deposition summaries, transcript summaries that if you kind of give it in that format, that kind of works that your certificate of authentication when you guys are providing it. if there's anything that we want to be able to use. for us when we do, if I have to transcribe from a different language, right from the Spanish to English for me to be able to use, I have an affidavit of certifying that this was done by this person at this time. I have proof that it was not me that did it. It was a third party. If you want to have that type of working for law firms, it's your output and probably certification of accuracy or because I don't think you want to do an affidavit that required to have a notary, that'd be too cost effective, but something to show that you guys are the one that completed it and can authenticate that this is correct to whatever percentage. I don't know what percentage you guys want to say of accuracy, but that would probably help out. it may, it may. It would help out for the ones that they ever have to use it in a arbitration, mediation or in a lawsuit type one if you want to work in there, if they already have in the beginning. And having that, I think that will probably get you a little bit better services for law firms. Does that make sense?"
        },
        {
            "response_id": "Altair Law_Cyrus Nazarian_5_2",
            "subject": "Subscription Model and Features",
            "question": "What subscription model and features would be compelling for legal-specific AI transcription packages?",
            "verbatim_response": "American Bar Association is usually they have a list of vendors when you're looking for different practice management, when you're looking for different, there's different software to use at a law firm. If you could find a way to get yourself into those forums where they have vetted you, they have approved you, that tends to be one they usually. And you can also put the ABA in each state. They also have their ones. for Georgia, I can go to the Georgia bar and it would have leading software and giving you a chart of all different areas. I need for a billing for a practice management, , just little stuff. looking I would look at those two aspects. Then you have there's a I forgot the name of the conference. Give me a second. See if I can find it. What is your name? Is it Andrew? No. Oh, no. I'm looking for the guy that I have. I have a software guy. That Arthur. That's his name. Arthur. That I have been working with for over 15 years. And every time I go to a new law firm, there's a tech show. It's an ABA tech show. That is probably where, because a lot of consultants go there, a lot of different law firms will probably send someone just to kind of see what is out there and available. But the ABA tech show that they have is probably where you want to also promote your items, because these consultants go to different law firms because we don't have time to go and sit and look at every law firm, vet it out, see, talk to them, saying the same thing over what we're looking for. We tend to go and use a lot of consultants, right? If the consultants have that information, then they'll be able to really push out for different law firms they talk to. And it could go from they deal with small law firms to big law firms. I know my guy does a lot of small and big. connecting with those type of consultants that's recommending software to law firms would probably be what we know. A lot of people know of Rev and can use it in a personal one. I just don't know the full on business case use as teams and zooms already adding that feature and people already having to pay for that enterprise for that particular program."
        }
    ]

def grade_enhanced_extraction():
    """Grade the enhanced extraction against manual output"""
    
    print("🎓 GRADING ENHANCED EXTRACTION: Altair Law vs Manual Output")
    print("=" * 80)
    
    # Get database responses
    db = SupabaseDatabase()
    df = db.get_stage1_data_responses(client_id='Rev')
    cyrus_responses = df[df['interviewee_name'].str.contains('Cyrus', case=False, na=False)]
    
    # Get manual output
    manual_responses = get_manual_output()
    
    print(f"📊 DATABASE RESPONSES: {len(cyrus_responses)}")
    print(f"📋 MANUAL RESPONSES: {len(manual_responses)}")
    print()
    
    # Analysis metrics
    metrics = {
        'quantity_score': 0,
        'quality_score': 0,
        'question_accuracy': 0,
        'content_preservation': 0,
        'complex_question_capture': 0,
        'subject_categorization': 0,
        'overall_grade': 'F'
    }
    
    # 1. Quantity Analysis
    quantity_ratio = len(cyrus_responses) / len(manual_responses)
    if quantity_ratio >= 1.5:
        metrics['quantity_score'] = 100
    elif quantity_ratio >= 1.2:
        metrics['quantity_score'] = 90
    elif quantity_ratio >= 1.0:
        metrics['quantity_score'] = 80
    elif quantity_ratio >= 0.8:
        metrics['quantity_score'] = 70
    else:
        metrics['quantity_score'] = 60
    
    print(f"📈 QUANTITY ANALYSIS:")
    print(f"   Database: {len(cyrus_responses)} responses")
    print(f"   Manual: {len(manual_responses)} responses")
    print(f"   Ratio: {quantity_ratio:.2f}")
    print(f"   Score: {metrics['quantity_score']}/100")
    print()
    
    # 2. Complex Question Capture Analysis
    complex_questions = [
        "Speed and cost were your top two priority. And you just mentioned layout",
        "When it comes to the transcription work they had done",
        "With accuracy rating so high. Are there any files",
        "When you went to find a vendor, did you already know about Rev"
    ]
    
    complex_found = 0
    for question in complex_questions:
        for _, row in cyrus_responses.iterrows():
            if question.lower() in row['question'].lower():
                complex_found += 1
                break
    
    complex_ratio = complex_found / len(complex_questions)
    metrics['complex_question_capture'] = complex_ratio * 100
    
    print(f"🔍 COMPLEX QUESTION CAPTURE:")
    print(f"   Complex questions found: {complex_found}/{len(complex_questions)}")
    print(f"   Success rate: {complex_ratio:.1%}")
    print(f"   Score: {metrics['complex_question_capture']:.1f}/100")
    print()
    
    # 3. Question Accuracy Analysis
    valid_questions = 0
    total_questions = len(cyrus_responses)
    
    for _, row in cyrus_responses.iterrows():
        question = row['question']
        if question != 'UNKNOWN' and len(question) > 10:
            valid_questions += 1
    
    question_accuracy = valid_questions / total_questions if total_questions > 0 else 0
    metrics['question_accuracy'] = question_accuracy * 100
    
    print(f"❓ QUESTION ACCURACY:")
    print(f"   Valid questions: {valid_questions}/{total_questions}")
    print(f"   Accuracy rate: {question_accuracy:.1%}")
    print(f"   Score: {metrics['question_accuracy']:.1f}/100")
    print()
    
    # 4. Content Preservation Analysis
    avg_response_length = cyrus_responses['verbatim_response'].str.len().mean()
    if avg_response_length >= 200:
        content_score = 100
    elif avg_response_length >= 150:
        content_score = 90
    elif avg_response_length >= 100:
        content_score = 80
    else:
        content_score = 70
    
    metrics['content_preservation'] = content_score
    
    print(f"📝 CONTENT PRESERVATION:")
    print(f"   Average response length: {avg_response_length:.0f} characters")
    print(f"   Score: {content_score}/100")
    print()
    
    # 5. Subject Categorization Analysis
    subjects = cyrus_responses['subject'].value_counts()
    diverse_subjects = len(subjects)
    if diverse_subjects >= 8:
        subject_score = 100
    elif diverse_subjects >= 6:
        subject_score = 90
    elif diverse_subjects >= 4:
        subject_score = 80
    else:
        subject_score = 70
    
    metrics['subject_categorization'] = subject_score
    
    print(f"🏷️ SUBJECT CATEGORIZATION:")
    print(f"   Unique subjects: {diverse_subjects}")
    print(f"   Score: {subject_score}/100")
    print()
    
    # Calculate overall grade
    weights = {
        'quantity_score': 0.25,
        'complex_question_capture': 0.30,
        'question_accuracy': 0.20,
        'content_preservation': 0.15,
        'subject_categorization': 0.10
    }
    
    overall_score = sum(metrics[key] * weights[key] for key in weights.keys())
    
    # Grade assignment
    if overall_score >= 95:
        grade = 'A+'
    elif overall_score >= 90:
        grade = 'A'
    elif overall_score >= 85:
        grade = 'A-'
    elif overall_score >= 80:
        grade = 'B+'
    elif overall_score >= 75:
        grade = 'B'
    elif overall_score >= 70:
        grade = 'B-'
    elif overall_score >= 65:
        grade = 'C+'
    elif overall_score >= 60:
        grade = 'C'
    else:
        grade = 'C-'
    
    metrics['overall_grade'] = grade
    
    print(f"🎯 OVERALL ASSESSMENT:")
    print(f"   Overall Score: {overall_score:.1f}/100")
    print(f"   Grade: {grade}")
    print()
    
    print(f"📊 DETAILED BREAKDOWN:")
    print(f"   Quantity: {metrics['quantity_score']:.1f}/100")
    print(f"   Complex Questions: {metrics['complex_question_capture']:.1f}/100")
    print(f"   Question Accuracy: {metrics['question_accuracy']:.1f}/100")
    print(f"   Content Preservation: {metrics['content_preservation']:.1f}/100")
    print(f"   Subject Categorization: {metrics['subject_categorization']:.1f}/100")
    print()
    
    # Improvement analysis
    print(f"🚀 IMPROVEMENT ANALYSIS:")
    print(f"   Previous grade: B+ (from earlier assessment)")
    print(f"   Current grade: {grade}")
    if overall_score > 85:
        print(f"   Status: SIGNIFICANT IMPROVEMENT! 🎉")
    elif overall_score > 80:
        print(f"   Status: MODERATE IMPROVEMENT 📈")
    else:
        print(f"   Status: NEEDS FURTHER REFINEMENT ⚠️")
    
    return metrics

if __name__ == "__main__":
    grade_enhanced_extraction() 