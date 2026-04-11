export interface CareType {
  slug: string
  label: string
  blurb: string
}

export const careTypes: CareType[] = [
  {
    slug: 'personal-care-companionship',
    label: 'Personal Care & Companionship',
    blurb: 'Help with bathing, dressing, routines, and day-to-day support at home.',
  },
  {
    slug: 'homemaker-support',
    label: 'Homemaker Support',
    blurb: 'Help with meals, laundry, light household tasks, and errands around the home.',
  },
  {
    slug: 'skilled-nursing',
    label: 'Skilled Nursing',
    blurb: 'Licensed nursing support for medications, wound care, monitoring, and clinical follow-up.',
  },
  {
    slug: 'physical-therapy',
    label: 'Physical Therapy',
    blurb: 'Support for strength, balance, mobility, and safer movement after illness or injury.',
  },
  {
    slug: 'occupational-therapy',
    label: 'Occupational Therapy',
    blurb: 'Help with daily activities, home routines, and adapting safely after health changes.',
  },
  {
    slug: 'speech-therapy',
    label: 'Speech Therapy',
    blurb: 'Support for communication, swallowing, and recovery after neurological or medical events.',
  },
  {
    slug: 'care-planning-social-support',
    label: 'Care Planning & Social Support',
    blurb: 'Guidance with care coordination, family planning, community resources, and transitions.',
  },
  {
    slug: 'respite-care',
    label: 'Respite Care',
    blurb: 'Short-term support that gives family caregivers time to rest or manage other needs.',
  },
  {
    slug: 'memory-care-support',
    label: 'Memory Care Support',
    blurb: 'Structured in-home support for members living with memory, dementia, or confusion concerns.',
  },
]

export const careTypeLabels = careTypes.map((careType) => careType.label)
