export const mockPulse = {
  pulse: {
    category: "ORS / Electral",
    merchant_count: 14,
    region: "Urban Mumbai",
    demand_multiplier: 4.0,
    headline_hi: "14 merchants ne ORS 4x stock kiya - IPL final kal hai",
    headline_en: "14 merchants increased ORS stock 4x - IPL final tomorrow",
    audio_url: "/audio/pulse_hi.mp3",
    viz_data: [14, 18, 22, 40, 56, 72, 96],
    privacy_note: "Aggregated across 14 merchants (k=5 minimum). +/-15% noise applied.",
  },
};

export const mockNewsTrends = {
  trends: [
    {
      id: "ipl_final",
      type: "cricket",
      icon: "cricket",
      title: "IPL Final - Kal Shaam 7:30pm",
      source: "NewsAPI + Network",
      body_hi: "Cold drinks, chips, namkeen demand 3-5x spike expected",
      body_en: "Cold drinks, chips, namkeen demand 3-5x spike expected",
      impact: [
        { item: "Cold Drinks", multiplier: "5x" },
        { item: "Chips/Namkeen", multiplier: "3x" },
      ],
      region: "Urban Mumbai",
      supporting_merchants: 22,
    },
    {
      id: "heat_wave",
      type: "weather",
      icon: "temperature",
      title: "Heat Wave - Mumbai, Thane, Pune",
      source: "NewsAPI + Network",
      body_hi: "42C agle 3 din - ORS demand 5x expected",
      body_en: "42C for the next 3 days - ORS demand 5x expected",
      impact: [
        { item: "ORS", multiplier: "5x" },
        { item: "Cold Drinks", multiplier: "3x" },
      ],
      region: "Urban Mumbai",
      supporting_merchants: 18,
    },
    {
      id: "eid",
      type: "festival",
      icon: "calendar",
      title: "Eid shopping window",
      source: "Festival Calendar",
      body_hi: "Sweets, dry fruits, seviyan aur gifting ki demand badhne ki sambhavna hai",
      body_en: "Expected rise in sweets, dry fruits, seviyan, and gifting demand",
      impact: [
        { item: "Seviyan", multiplier: "4x" },
        { item: "Dry Fruits", multiplier: "2x" },
      ],
      region: "Urban Mumbai",
      supporting_merchants: 16,
    },
    {
      id: "janmashtami",
      type: "festival",
      icon: "calendar",
      title: "Janmashtami preparation",
      source: "Festival Calendar",
      body_hi: "Milk, curd, butter, sweets aur pooja items ki demand badh sakti hai",
      body_en: "Milk, curd, butter, sweets, and pooja items can see higher demand",
      impact: [
        { item: "Milk/Curd", multiplier: "3x" },
        { item: "Sweets", multiplier: "3x" },
      ],
      region: "Urban Mumbai",
      supporting_merchants: 12,
    },
  ],
};

export const mockGroupBuy = {
  active_groups: [
    {
      id: "ors_andheri_001",
      item: "ORS Electral",
      merchants_count: 4,
      discount_percent: 18,
      closes_in_minutes: 120,
      regular_price: 10.0,
      group_price: 8.2,
      minimum_units: 30,
      privacy_note: "Other merchants' identities never revealed",
    },
  ],
};

export const mockBroadcast = {
  status: "queued",
  messages: {
    "hi-IN": "Namaste! Kal IPL Final hai - cold drinks aur snacks aaj hi le lo. 10% off Rs 200+ par!",
    "mr-IN": "Namaskar! Udya IPL Final aahe - cold drinks aaj gheun ja. 10% soot!",
    "gu-IN": "Namaste! Kale IPL Final che - cold drinks lo. 10% chhut!",
    "en-IN": "Hi! IPL Final tomorrow - get your snacks today. 10% off on Rs 200+!",
  },
  estimated_reach: 12400,
  channel: "paytm_ads",
  campaign_id: "mock_ads_phase1_001",
  privacy_note: "No customer PII exposed. Paytm Ads handles targeting on platform side.",
};
