import { useState } from 'react';
import { CLOUD_INSTRUCTIONS } from '@/data/instructionsData';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export function InstructionsPage() {
    const [activeTab, setActiveTab] = useState<keyof typeof CLOUD_INSTRUCTIONS>('gcp');
    const data = CLOUD_INSTRUCTIONS[activeTab];

    if (!data) return null;

    const tabs = Object.keys(CLOUD_INSTRUCTIONS) as (keyof typeof CLOUD_INSTRUCTIONS)[];

    return (
        <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Cloud Setup Instructions</h1>
                <p className="text-muted-foreground mt-2">
                    Detailed guides for configuring cost export and API access for your cloud providers.
                </p>
            </div>

            <div className="flex-1 flex flex-col min-h-0">
                <div className="grid w-full grid-cols-3 max-w-md mb-4 bg-muted p-1 rounded-lg">
                    {tabs.map((key) => (
                        <Button
                            key={key}
                            variant={activeTab === key ? 'default' : 'ghost'}
                            size="sm"
                            onClick={() => setActiveTab(key)}
                            className="w-full"
                        >
                            {key === 'gcp' ? 'GCP' : key === 'aws' ? 'AWS' : 'Azure'}
                        </Button>
                    ))}
                </div>

                <Card className="flex-1 flex flex-col min-h-0 overflow-hidden">
                    <CardHeader className="flex-shrink-0">
                        <CardTitle>{data.title}</CardTitle>
                        <CardDescription className="text-base">{data.overview}</CardDescription>
                    </CardHeader>

                    <CardContent className="flex-1 overflow-y-auto px-6 pb-6">
                        <div className="space-y-8 max-w-4xl pt-2">
                            {data.sections.map((section, idx) => (
                                <div key={idx} className="space-y-4">
                                    <h3 className="text-xl font-semibold tracking-tight border-b pb-2">
                                        {section.title}
                                    </h3>

                                    <div className="space-y-4">
                                        {section.items.map((item, i) => (
                                            <div key={i} className="space-y-2">
                                                {item.label && (
                                                    <h4 className="font-medium text-sm text-foreground/90">
                                                        {item.label}
                                                    </h4>
                                                )}

                                                {item.text && (
                                                    <p className="text-sm text-muted-foreground leading-relaxed">
                                                        {item.text}
                                                    </p>
                                                )}

                                                {item.list && (
                                                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1 ml-2">
                                                        {item.list.map((li, l) => (
                                                            <li key={l}>{li}</li>
                                                        ))}
                                                    </ul>
                                                )}

                                                {item.code && (
                                                    <div className="bg-slate-950 text-slate-50 rounded-lg p-4 font-mono text-xs overflow-x-auto border border-slate-800 shadow-sm">
                                                        <pre className="whitespace-pre-wrap break-words">
                                                            {item.code}
                                                        </pre>
                                                    </div>
                                                )}

                                                {item.note && (
                                                    <div className="bg-yellow-500/10 border-l-4 border-yellow-500/50 p-3 rounded-r text-sm text-yellow-500/90 italic">
                                                        {item.note}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
