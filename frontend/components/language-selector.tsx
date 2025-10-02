"use client"

import { Button } from "@/components/ui/button"
import { Check } from "lucide-react"

interface LanguageSelectorProps {
  selectedLanguage: string
  onSelectLanguage: (language: string) => void
  onClose: () => void
}

const languages = [
  { code: "en", name: "English", native: "English" },
  { code: "hi", name: "Hindi", native: "हिन्दी" },
  { code: "pa", name: "Punjabi", native: "ਪੰਜਾਬੀ" },
  { code: "mr", name: "Marathi", native: "मराठी" },
  { code: "gu", name: "Gujarati", native: "ગુજરાતી" },
  { code: "ta", name: "Tamil", native: "தமிழ்" },
  { code: "te", name: "Telugu", native: "తెలుగు" },
  { code: "kn", name: "Kannada", native: "ಕನ್ನಡ" },
  { code: "bn", name: "Bengali", native: "বাংলা" },
  { code: "ml", name: "Malayalam", native: "മലയാളം" },
]

export default function LanguageSelector({ selectedLanguage, onSelectLanguage, onClose }: LanguageSelectorProps) {
  return (
    <div className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-b-2 border-green-200/50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Select Language</h3>
        <Button variant="ghost" size="sm" onClick={onClose} className="hover:bg-green-100 text-gray-700">
          Close
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {languages.map((lang) => (
          <Button
            key={lang.code}
            variant={selectedLanguage === lang.name ? "default" : "outline"}
            className={`h-auto py-4 px-4 flex flex-col items-center gap-2 relative group hover:scale-105 transition-transform ${
              selectedLanguage === lang.name
                ? "bg-gradient-to-br from-green-600 to-emerald-600 text-white border-green-300"
                : "border-green-300 hover:bg-green-100 hover:border-green-400 text-gray-800"
            }`}
            onClick={() => onSelectLanguage(lang.name)}
          >
            {selectedLanguage === lang.name && (
              <div className="absolute top-2 right-2">
                <Check className="h-4 w-4" />
              </div>
            )}
            <span className="text-2xl">{lang.native}</span>
            <span className="text-xs">{lang.name}</span>
          </Button>
        ))}
      </div>
    </div>
  )
}
